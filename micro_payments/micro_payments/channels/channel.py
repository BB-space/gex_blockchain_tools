import logging
from copy import copy
from enum import Enum

from gex_chain.crypto import sign_balance_proof
from gex_chain.utils import convert_balances_data, check_overspend, BalancesData
from gex_chain.utils import get_data_for_token

log = logging.getLogger(__name__)


class Channel:

    class State(Enum):
        open = 1
        settling = 2
        closed = 3

    def __init__(
            self,
            client,
            sender: str,
            block: int,
            deposit=0,
            channel_fee=0,
            random_n=b'',
            balances_data=None,
            state=State.open
    ):

        self._balances_data = [('0x0', 0)]
        self._balances_data_converted = [0]
        self._balances_data_sig = None

        self.client = client
        self.sender = sender.lower()
        self.deposit = deposit
        self.block = block
        self.random_n = random_n
        self.channel_fee = channel_fee
        if balances_data is not None:
            self.balances_data = balances_data
        self.state = state

        assert self.block is not None

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
                craw['state']
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
                'state': c.state

            } for c in channels
        ]

    @property
    def balances_data(self):
        return self._balances_data

    @property
    def balances_data_converted(self):
        return self._balances_data_converted

    @balances_data.setter
    def balances_data(self, value):
        pass

    @property
    def balance_sig(self):
        return self._balances_data_sig

    def close(self):
        """
        Attempts to request close on a channel. An explicit balance can be given to override the
        locally stored balance signature. Blocks until a confirmation event is received or timeout.
        """
        if self.state != Channel.State.open:
            log.error('Channel must be open to request a close.')
            return
        log.info('Requesting close of channel created at block #{}.'.format(self.block))
        current_block = self.client.web3.eth.blockNumber

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'close', [self.sender, self.block, self.balances_data_converted, self.balance_sig]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for close confirmation event...')
        event = self.client.channel_manager_proxy.get_channel_close_requested_event_blocking(
            self.sender, self.block, current_block - 1
        )

        if event:
            log.info('Successfully sent channel close request in block {}.'.format(
                event['blockNumber']
            ))
            self.state = Channel.State.settling
            return event
        else:
            log.error('No event received.')
            return None

    def settle(self):
        """
        Attempts to settle a channel that has passed its settlement period. If a channel cannot be
        settled yet, the call is ignored with a warning. Blocks until a confirmation event is
        received or timeout.
        """
        if self.state != Channel.State.settling:
            log.error('Channel must be in the settlement period to settle.')
            return None
        log.info('Attempting to settle channel created at block #{}.'.format(self.block))

        settle_block = self.client.channel_manager_proxy.get_settle_timeout(self.sender, self.block)

        current_block = self.client.web3.eth.blockNumber
        wait_remaining = settle_block - current_block
        if wait_remaining > 0:
            log.warning('{} more blocks until this channel can be settled. Aborting.'.format(
                wait_remaining
            ))
            return None

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'settle', [self.sender, self.block]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for settle confirmation event...')
        event = self.client.channel_manager_proxy.get_channel_settle_event_blocking(
            self.sender, self.block, current_block
        )

        if event:
            log.info('Successfully settled channel in block {}.'.format(event['blockNumber']))
            self.state = Channel.State.closed
            self.client.channel = None
            return event
        else:
            log.error('No event received.')
            return None

    def is_valid(self) -> bool:
        return self.sign() == self.balance_sig and not check_overspend(self.deposit, self._balances_data)[0]
