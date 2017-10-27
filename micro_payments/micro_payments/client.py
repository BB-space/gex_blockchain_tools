import json
import logging
import os

import click
import filelock
from gex_chain.crypto import privkey_to_addr
from gex_chain.utils import get_private_key, get_data_for_token
from micro_payments.config import GAS_LIMIT, GAS_PRICE, \
    NETWORK_NAMES, APP_FOLDER, DATA_FILE_NAME
from micro_payments.contract_proxy import ContractProxy, ChannelContractProxy
from web3 import Web3
from web3.providers.rpc import RPCProvider

from micro_payments.channels.sender_channel import SenderChannel
from micro_payments.channels.maintainer_channel import MaintainerChannel
from micro_payments.channels.channel import Channel

log = logging.getLogger(__name__)


class Client:
    def __init__(
            self,
            privkey: str = None,
            key_path: str = None,
            key_password_path: str = None,
            channel_manager_address: str = None,
            token_address: str = None,
            rpc: RPCProvider = None,
            web3: Web3 = None,
            channel_manager_proxy: ChannelContractProxy = None,
            token_proxy: ContractProxy = None,
            rpc_endpoint: str = '127.0.0.1',
            rpc_port: int = 8545,
            data_file_path: str = DATA_FILE_NAME

    ) -> None:
        assert privkey or key_path
        assert not privkey or isinstance(privkey, str)

        # Plain copy initializations.
        self.privkey = privkey
        self.datadir = APP_FOLDER
        self.channel_manager_address = channel_manager_address
        self.token_address = token_address
        self.web3 = web3
        self.channel_manager_proxy = channel_manager_proxy
        self.token_proxy = token_proxy

        # Load private key from file if none is specified on command line.
        if not privkey:
            self.privkey = get_private_key(key_path, key_password_path)
            assert self.privkey is not None

        os.makedirs(self.datadir, exist_ok=True)
        assert os.path.isdir(self.datadir)

        self.account = privkey_to_addr(self.privkey)
        self.sender_channel = None
        self.maintaining_channels = []
        self.receiving_channels = []

        # Create web3 context if none is provided, either by using the proxies' context or creating
        # a new one.
        if not web3:
            if channel_manager_proxy:
                self.web3 = channel_manager_proxy.web3
            elif token_proxy:
                self.web3 = token_proxy.web3
            else:
                if not rpc:
                    rpc = RPCProvider(rpc_endpoint, rpc_port)
                self.web3 = Web3(rpc)

        # Create missing contract proxies.
        data_file_path = os.path.join(self.datadir, data_file_path)
        if not channel_manager_proxy or not token_proxy:
            with open(data_file_path) as abi_file:
                data_file = json.load(abi_file)
            if not channel_manager_address:
                channel_manager_address = data_file['channels_address']
            if not token_address:
                token_address = data_file['token_address']

            if not channel_manager_proxy:
                channel_manager_abi = data_file['channels_abi']
                self.channel_manager_proxy = ChannelContractProxy(
                    self.web3,
                    self.privkey,
                    channel_manager_address,
                    channel_manager_abi,
                    GAS_PRICE,
                    GAS_LIMIT
                )

            if not token_proxy:
                token_abi = data_file['token_abi']
                self.token_proxy = ContractProxy(
                    self.web3, self.privkey, token_address, token_abi, GAS_PRICE, GAS_LIMIT
                )

        assert self.web3
        assert self.channel_manager_proxy
        assert self.token_proxy
        assert self.channel_manager_proxy.web3 == self.web3 == self.token_proxy.web3

        net_id = self.web3.version.network
        self.balances_filename = 'balances_{}_{}.json'.format(
            NETWORK_NAMES.get(net_id, net_id), self.account[:10]
        )

        self.filelock = filelock.FileLock(os.path.join(self.datadir, self.balances_filename))
        self.filelock.acquire(timeout=0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.filelock.release()

    def register_maintainer_listeners(self):
        pass

    def open_channel(self, deposit: int, channel_fee: int):
        """
        Attempts to open a new channel with the given deposit. Blocks until the
        creation transaction is found in a pending block or timeout is reached. The new channel is returned.
        """
        assert isinstance(deposit, int)
        assert channel_fee > 0
        assert channel_fee * 3 < deposit
        assert self.sender_channel is None or self.sender_channel.state == Channel.State.closed
        assert deposit > 0

        token_balance = self.token_proxy.contract.call().balanceOf(self.account)
        if token_balance < deposit:
            log.error(
                'Insufficient tokens available for the specified deposit ({}/{})'
                    .format(token_balance, deposit)
            )

        current_block = self.web3.eth.blockNumber
        log.info('Creating channel with an initial deposit of {} @{}'.format(
            deposit, current_block
        ))

        data = get_data_for_token(0, channel_fee)
        tx = self.token_proxy.create_signed_transaction(
            'transfer', [self.channel_manager_address, deposit, data]
        )
        self.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for channel creation event on the blockchain...')
        event = self.channel_manager_proxy.get_channel_created_event_blocking(
            self.account, current_block + 1
        )

        if event:
            log.info('Event received. Channel created in block {}.'.format(event['blockNumber']))
            channel = SenderChannel(
                self,
                event['args']['_sender'],
                event['blockNumber'],
                event['args']['_deposit'],
                event['args']['_channel_fee'],
                event['args']['_random_n']
            )
            self.sender_channel = channel
        else:
            log.info('Error: No event received.')
            channel = None

        return channel

    def maintain_channel(self, sender: str, open_block: int):  # TODO create a channel if I'm the first one
        channel = MaintainerChannel(self, sender, open_block)

        current_block = self.web3.eth.blockNumber
        tx = self.channel_manager_proxy.create_signed_transaction(
            'registerMaintainer', [sender, open_block]
        )

        self.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for channel creation event on the blockchain...')
        event = self.channel_manager_proxy.get_channel_created_event_blocking(
            self.account, current_block + 1
        )
        if event:
            self.maintaining_channels.append(channel)
            # new listener for channel
            return channel
        else:
            log.error('No event received')
            return None

    def get_receiving_channel(self, sender):
        pass

    def add_receiving_channel(self, sender, open_block):
        pass
