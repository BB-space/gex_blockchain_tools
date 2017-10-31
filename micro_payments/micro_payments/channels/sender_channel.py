import logging
from copy import copy

from gex_chain.crypto import sign_balance_proof
from gex_chain.utils import convert_balances_data, check_overspend, BalancesData
from gex_chain.utils import get_data_for_token
from micro_payments.channels.channel import Channel
from micro_payments.kafka_lib.sender_kafka import SenderKafka

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
            kafka_sender: SenderKafka = None
    ):

        super().__init__(client, sender, block, deposit, channel_fee, random_n, balances_data, state)
        self._kafka_sender = kafka_sender

    @property
    def balances_data(self):
        return self._balances_data

    @balances_data.setter
    def balances_data(self, balances_data: BalancesData):
        self._balances_data = balances_data
        self._balances_data_sig = self.sign()
        self._balances_data_converted = convert_balances_data(balances_data)

    def set_kafka_sender(self, kafka_sender: SenderKafka):
        self._kafka_sender = kafka_sender

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
                'Insufficient tokens available for the specified topup ({}/{})'
                .format(token_balance, deposit)
            )

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

    def create_transfer(self, balances_data: BalancesData):  # TODO
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
        message = {'balances_data': self.balances_data, 'balances_sig': self._balances_data_sig}
        self._kafka_sender.send(message) # TODO tes

        return self.balance_sig

    def is_suitable(self, value: int):
        return check_overspend(self.deposit, self._balances_data)[1] >= value
