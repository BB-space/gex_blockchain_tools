import logging
from enum import Enum
from typing import List

from gex_chain.utils import check_overspend
from gex_chain.crypto import eth_verify, get_balance_message

log = logging.getLogger(__name__)


def check_sign_with_logger(logger):
    def check_sign(f):
        def wrapper(self, balances_data, balances_data_sig):
            if self.sender != eth_verify(
                    balances_data_sig,
                    get_balance_message(self.sender, self.block, balances_data)
            ):
                logger.error('The given balances data and signature does not match')
                return None
            return f(self, balances_data, balances_data_sig)

        return wrapper

    return check_sign


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
            state=State.open,
            topic_holder=None
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
        self._state = state
        self.topic_holder = topic_holder
        self.close_listener = None

        assert self.block is not None
        self.update()

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
                Channel.State(craw['state']),
                craw['topic_holder']
            )
            for craw in channels_raw
        ]

    @staticmethod
    def serialize(channels: List[__class__]):
        return [
            {
                'sender': c.sender,
                'deposit': c.deposit,
                'block': c.block,
                'channel_fee': c.channel_fee,
                'random_n': c.random_n,
                'balances_data': c.balances_data,
                'state': c.state,
                'topic_holder': c.topic_holder

            } for c in channels
        ]

    @property
    def topic_name(self):
        return "{}_{}".format(self.sender, self.block)

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

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        assert new_state > self._state
        self._state = new_state

    def update(self):
        try:
            info = self.client.channel_manager_proxy.contract.call().getChannelInfo(self.sender, self.block)
            self.deposit = info[1]
            self.channel_fee = info[3]
            self.topic_holder = info[4]
        except Exception as ex:
            log.error('Could not get Channel info. Either the channel does not exist, or no maintainers are '
                      'registered yet')
            return

        try:
            self.client.channel_manager_proxy.contract.call().getChannelInfo(self.sender, self.block)
            self.state = Channel.State.settling
        except Exception as ex:
            log.error('Could not get Closing requests info. The request does not exist')

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
            self.sender, self.block, current_block + 1
        )

        if event:
            log.info('Successfully sent channel close request in block {}.'.format(
                event['blockNumber']
            ))
            self.state = Channel.State.settling
            if self.close_listener:
                self.close_listener.stop()
                del self.close_listener
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
            self.sender, self.block, current_block + 1
        )

        if event:
            log.info('Successfully settled channel in block {}.'.format(event['blockNumber']))
            self.state = Channel.State.closed
            self.client.channel = None
            return event
        else:
            log.error('No event received.')
            return None

    def close_callback(self, event):
        assert event['event'] == 'ChannelCloseRequested'
        event_args = event['args']
        assert event_args['_sender'] == self.sender
        assert event_args['_open_block_number'] == self.block
        self.state = Channel.State.settling
        log.info('Channel with sender {} open on block {} was settled in block {}. Removing channel'.format(
            self.sender, self.block, event['blockNumber']
        ))

    def is_valid(self) -> bool:
        return self.sign() == self.balance_sig and not check_overspend(self.deposit, self._balances_data)[0]
