import json
import logging
from copy import copy

from gex_chain.crypto import sign_balance_proof
from gex_chain.utils import convert_balances_data, check_overspend, BalancesData, is_cheating
from gex_chain.utils import get_data_for_token
from micro_payments.channels.channel import Channel, check_sign_with_logger
from micro_payments.kafka_lib.receiving_kafka import ReceivingKafka

log = logging.getLogger(__name__)


class MaintainerChannel(Channel):
    """
    Channel used by the maintainer
    """

    def __init__(
            self,
            client,
            sender: str,
            block: int,
            deposit=0,
            channel_fee=0,
            random_n=b'',
            balances_data=None,
            state=Channel.State.open,
            topic_holder=None,
            receiving_kafka: ReceivingKafka = None
    ):
        Channel.__init__(
            self,
            client,
            sender,
            block,
            deposit,
            channel_fee,
            random_n,
            balances_data,
            state,
            topic_holder
        )
        self._receiving_kafka = receiving_kafka

    @property
    def balances_data(self):
        return self._balances_data

    @balances_data.setter
    def balances_data(self, value: BalancesData):
        log.error('You cannot set new data, use set_new_balances')
        return

    @property
    def receiving_kafka(self):
        return self._receiving_kafka

    def create_receiving_kafka(self):
        if self._receiving_kafka is not None and isinstance(self._receiving_kafka, ReceivingKafka):
            log.error('Kafka is already set, remove it first')
            return
        self._receiving_kafka = ReceivingKafka(
            self.topic_name,
            self.client.account,
            '',
            self.client.get_node_ip(self.topic_holder)
        )

    def stop_kafka(self):
        if self._receiving_kafka is not None and \
                isinstance(self._receiving_kafka, ReceivingKafka) and self._receiving_kafka.running:
            self._receiving_kafka.stop()
            del self._receiving_kafka
        else:
            log.error('Kafka is not set or not running')

    def force_remove_kafka(self):
        if self._receiving_kafka is not None:
            try:
                self._receiving_kafka.stop()
            except:
                log.error('There was an error stopping Receiving kafka')
            del self._receiving_kafka

    def config_and_start_kafka(self):
        if self._receiving_kafka is None or not isinstance(self._receiving_kafka, ReceivingKafka):
            log.error('Kafka receiver is not set or set incorrectly')
            return

        if self._receiving_kafka.running:
            log.error('Kafka receiver is already running')
            return

        if self._receiving_kafka.stopped:
            log.error('Kafka receiver was stopped, create a new one to continue')
            return

        def kafka_helper(message):
            message_value = json.loads(message.value.decode('utf-8'))
            self.set_new_balances(**message_value)  # TODO test

        self._receiving_kafka.add_listener_function(kafka_helper)
        self._receiving_kafka.start()

    def _is_cheating(self, balances_data) -> bool:
        if check_overspend(self.deposit, balances_data)[0]:
            return True
        return is_cheating(self.balances_data, balances_data)

    def _report_cheating(self, balances_data: BalancesData, balances_data_sig: bytes):
        if self.state == Channel.State.closed:
            log.error('Channel must not be closed to report cheating.')
            return None

        log.info('Reporting cheating to a channel created at block #{} by {} '.format(
            self.block, self.sender
        ))
        current_block = self.client.web3.eth.blockNumber

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'reportCheating',
            [
                self.sender,
                self.block,
                self.balances_data_converted,
                self.balance_sig,
                balances_data,
                balances_data_sig
            ]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for CheatingReported confirmation event...')
        event = self.client.channel_manager_proxy.get_cheating_reported_event_blocking(
            self.sender,
            self.block,
            current_block + 1
        )

        if event:
            log.info('Successfully reported cheating in block {}.'.format(event['blockNumber']))
            return event
        else:
            log.error('No event received.')
            return None

    @check_sign_with_logger(log)
    def set_new_balances(self, balances_data: BalancesData, balances_data_sig: bytes):
        cheating = self._is_cheating(balances_data)
        if cheating is None:
            log.error('Got wrong new balances data (probably wrong order)')
            return
        if cheating:
            self._report_cheating(balances_data, balances_data_sig)
        else:
            self._balances_data = balances_data
            self._balances_data_converted = convert_balances_data(balances_data)
            self._balances_data_sig = balances_data_sig

    def submit_later_transaction(self):
        if self.balances_data_converted is None:
            log.error('No data to send!')
            return None

        if self.state != Channel.State.settling:
            log.error('Channel must be in settlement period to submit a later transfer.')
            return None

        log.info('Sending a new transaction to a channel created at block #{} by {} '.format(
            self.block, self.sender
        ))
        current_block = self.client.web3.eth.blockNumber

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'submitLaterTransaction', [self.sender, self.block, self.balances_data_converted, self.balance_sig]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for ClosingBalancesChanged confirmation event...')
        event = self.client.channel_manager_proxy.get_channel_closing_balances_changed_event_blocking(
            self.sender,
            self.block,
            current_block + 1
        )

        if event:
            log.info('Successfully submitted new transaction in block {}.'.format(event['blockNumber']))
            return event
        else:
            log.error('No event received.')
            return None
