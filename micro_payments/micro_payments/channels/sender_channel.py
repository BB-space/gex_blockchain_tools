import logging
from copy import copy

from gex_chain.crypto import sign_balance_proof
from gex_chain.utils import convert_balances_data, check_overspend, BalancesData
from gex_chain.utils import get_data_for_token
from micro_payments.channels.channel import Channel
from micro_payments.kafka_lib.sender_kafka import SenderKafka
from micro_payments.event_listener.listener import Listener

log = logging.getLogger(__name__)


class SenderChannel(Channel):
    """
    Channel used by the sender
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
            kafka_sender: SenderKafka = None
    ):

        super().__init__(client, sender, block, deposit, channel_fee, random_n, balances_data, state, topic_holder)
        self._kafka_sender = kafka_sender
        self._topic_event_listener = None  # type: Listener

    @staticmethod
    def deserialize(client, channels_raw: dict):
        return [
            Channel(
                client,
                craw['sender'],
                craw['block'],
                craw['deposit'],
                craw['channel_fee'],
                craw['random_n'],
                craw['balances_data'],
                Channel.State(craw['state'])
            )
            for craw in channels_raw
        ]

    @staticmethod
    def serialize(channels):
        return [
            {
                'sender': c.sender,
                'deposit': c.deposit,
                'block': c.block,
                'channel_fee': c.channel_fee,
                'random_n': c.random_n,
                'balances_data': c.balances_data,
                'balances_data_sig': c.balances_data_sig,
                'state': c.state

            } for c in channels
        ]

    @property
    def balances_data(self):
        return self._balances_data

    @balances_data.setter
    def balances_data(self, balances_data: BalancesData):
        self._balances_data = balances_data
        self._balances_data_sig = self.sign()
        self._balances_data_converted = convert_balances_data(balances_data)

    @property
    def kafka_sender(self):
        return self._kafka_sender

    def _create_kafka_sender(self, bootstrap_server):
        if self._kafka_sender is not None:
            self._kafka_sender.close()
            del self._kafka_sender
        self._kafka_sender = SenderKafka(self.topic_name, bootstrap_server)

    def topic_created_callback(self, event):
        assert event['event'] == 'ChannelTopicCreated'
        event_args = event['args']
        assert event_args['_sender'] == self.sender
        assert event_args['_open_block_number'] == self.block
        self._topic_event_listener.stop()
        del self._topic_event_listener
        self.topic_holder = event_args['_topic_holder']
        ip = self.client.get_node_ip(self.topic_holder)
        self._create_kafka_sender(ip)

    def set_topic_event_listener(self, listener: Listener):
        if listener.stopped:
            log.error('The listener you are trying to set was stopped')
            return
        self._topic_event_listener = listener

    def sign(self):
        return sign_balance_proof(self.client.privkey, self.sender, self.block, self._balances_data)

    def top_up(self, deposit):
        """
        Attempts to increase the deposit in an existing channel. Block until confirmation.
        """
        if self.state != Channel.State.open:
            log.error('Channel must be open to be topped up.')
            return

        token_balance = self.client.token_proxy.contract.call().balanceOf(self.client.account)
        if token_balance < deposit:
            log.error(
                'Insufficient tokens available for the specified top up ({}/{})'
                .format(token_balance, deposit)
            )
            return

        log.info('Topping up channel created at block #{} by {} tokens.'.format(
            self.block, deposit
        ))
        current_block = self.client.web3.eth.blockNumber

        data = get_data_for_token(1, self.block)
        tx = self.client.token_proxy.create_signed_transaction(
            'transfer', [self.client.channel_manager_address, deposit, data]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for topup confirmation event...')
        event = self.client.channel_manager_proxy.get_channel_topped_up_event_blocking(
            self.sender,
            self.block,
            current_block + 1
        )

        if event:
            log.info('Successfully topped up channel in block {}.'.format(event['blockNumber']))
            self.deposit = event['args']['_deposit']
            return event
        else:
            log.error('No event received.')
            return None

    def create_transfer(self, balances_data: BalancesData):
        """
        Updates the given channel's balance and balance signature with the new value. The signature
        is returned and stored in the channel state.
        """
        if self._kafka_sender is None or not isinstance(self._kafka_sender, SenderKafka):
            log.error('Kafka sender is not set or is set incorrectly')
            return None

        for pair in balances_data:
            assert pair[1] >= 0

        overspent, leftover = check_overspend(copy(self.deposit), balances_data)
        if overspent:
            log.error(
                'Insufficient funds on channel. Need {} more'
                .format(-leftover)
            )
            return None

        log.info('Signing new transfer {} on channel created at block #{}.'.format(
            balances_data, self.block
        ))

        if self.state == Channel.State.closed:
            log.error('Channel must be open to create a transfer.')
            return None

        self.balances_data = balances_data
        message = {'balances_data': self.balances_data, 'balances_data_sig': self._balances_data_sig}
        self._kafka_sender.send(message)  # TODO test

        return self.balance_sig

    def is_suitable(self, value: int):
        return check_overspend(self.deposit, self._balances_data)[1] >= value
