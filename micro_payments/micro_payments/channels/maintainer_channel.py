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
            receiving_kafka: ReceivingKafka = None
    ):
        Channel.__init__(self, client, sender, block, deposit, channel_fee, random_n, balances_data, state)
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

    @receiving_kafka.setter
    def receiving_kafka(self, receiving_kafka: ReceivingKafka):
        if self._receiving_kafka is not None:
            self._receiving_kafka.stop()
            del self._receiving_kafka
        self._receiving_kafka = receiving_kafka

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
