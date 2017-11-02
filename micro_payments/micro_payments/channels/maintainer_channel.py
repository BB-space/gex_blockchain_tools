import json
import logging

from gex_chain.utils import convert_balances_data, check_overspend, BalancesData, is_cheating,\
    get_balances_data, compare_balances_data
from micro_payments.channels.channel import Channel, check_sign_with_logger
from micro_payments.kafka_lib.receiving_kafka import ReceivingKafka
from micro_payments.event_listener.listener import Listener

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
        self._event_listeners = []

    @property
    def balances_data(self):
        return self._balances_data

    @balances_data.setter
    def balances_data(self, value: BalancesData):
        log.error('One does not simply set new data, use set_new_balances')
        return

    @property
    def receiving_kafka(self):
        return self._receiving_kafka

    def _if_not_closed(self, f):
        def decorated(*args, **kwargs):
            if self.state == Channel.State.closed:
                log.error('The channel is already closed')
                return None
            return f(*args, **kwargs)
        return decorated

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
            except Exception as ex:
                log.error('There was an error stopping Receiving kafka: {}'.format(ex))
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

    @_if_not_closed
    @check_sign_with_logger(log)
    def set_new_balances(self, balances_data: BalancesData, balances_data_sig: bytes):
        cheating = self._is_cheating(balances_data)
        if cheating is None:
            log.error('Got wrong balances data (probably wrong order)')
            return None
        if cheating:
            self._report_cheating(balances_data, balances_data_sig)
            return None
        else:
            balances_diff = compare_balances_data(self.balances_data, balances_data)
            if balances_diff and balances_diff > 0:
                self._balances_data = balances_data
                self._balances_data_converted = convert_balances_data(balances_data)
                self._balances_data_sig = balances_data_sig
            return self.balances_data

    @_if_not_closed
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

    def balances_changed_callback(self, event):
        assert event['event'] == 'ClosingBalancesChanged'
        event_args = event['args']
        assert event_args['_sender'] == self.sender
        assert event_args['_open_block_number'] == self.block
        new_balances = get_balances_data(event_args['_payment_data'])
        if new_balances == self.balances_data:
            return
        else:
            balances_diff = compare_balances_data(self.balances_data, new_balances)
            if balances_diff and balances_diff < 0:
                self.submit_later_transaction()

    def settle_callback(self, event):
        assert event['event'] == 'ChannelSettled'
        event_args = event['args']
        assert event_args['_sender'] == self.sender
        assert event_args['_open_block_number'] == self.block
        for listener in self._event_listeners:
            listener.stop()
        log.info('Channel with sender {} open on block {} was settled in block {}. Removing channel'.format(
            self.sender, self.block, event['blockNumber']
        ))
        self.client.maintaining_channels.remove(self)

    @_if_not_closed
    def add_listener(self, listener: Listener):
        if self.state != Channel.State.closed:
            self._event_listeners.append(listener)