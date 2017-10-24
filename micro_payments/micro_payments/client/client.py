import json
import logging
import os
from typing import List

import click
import filelock
from eth_utils import decode_hex, is_same_address
from web3 import Web3
from web3.providers.rpc import RPCProvider

from gex_chain.utils import get_private_key, get_data_for_token
from micro_payments.config import CHANNEL_MANAGER_ADDRESS, TOKEN_ADDRESS, GAS_LIMIT, GAS_PRICE, \
    NETWORK_NAMES
from micro_payments.contract_proxy import ContractProxy, ChannelContractProxy
from micro_payments.crypto import privkey_to_addr
from .channel import Channel

CHANNEL_MANAGER_ABI_NAME = 'MicroTransferChannels'
TOKEN_ABI_NAME = 'GEXToken'

log = logging.getLogger(__name__)





class Client:
    def __init__(
            self,
            privkey: str = None,
            key_path: str = None,
            key_password_path: str = None,
            datadir: str = click.get_app_dir('micro_payments'), # TODO
            channel_manager_address: str = CHANNEL_MANAGER_ADDRESS,
            token_address: str = TOKEN_ADDRESS,
            rpc: RPCProvider = None,
            web3: Web3 = None,
            channel_manager_proxy: ChannelContractProxy = None,
            token_proxy: ContractProxy = None,
            rpc_endpoint: str = 'localhost',
            rpc_port: int = 8545,
            contract_abi_path: str = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 'data/contracts.json'
            )
    ) -> None:
        assert privkey or key_path
        assert not privkey or isinstance(privkey, str)

        # Plain copy initializations.
        self.privkey = privkey
        self.datadir = datadir
        self.channel_manager_address = channel_manager_address
        self.token_address = token_address
        self.web3 = web3
        self.channel_manager_proxy = channel_manager_proxy
        self.token_proxy = token_proxy

        # Load private key from file if none is specified on command line.
        if not privkey:
            self.privkey = get_private_key(key_path, key_password_path)
            assert self.privkey is not None

        os.makedirs(datadir, exist_ok=True)
        assert os.path.isdir(datadir)

        self.account = privkey_to_addr(self.privkey)
        self.channel = None  # type: Channel

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
        if not channel_manager_proxy or not token_proxy:
            with open(contract_abi_path) as abi_file:
                contract_abis = json.load(abi_file)

            if not channel_manager_proxy:
                channel_manager_abi = contract_abis[CHANNEL_MANAGER_ABI_NAME]['abi']
                self.channel_manager_proxy = ChannelContractProxy(
                    self.web3,
                    self.privkey,
                    channel_manager_address,
                    channel_manager_abi,
                    GAS_PRICE,
                    GAS_LIMIT
                )

            if not token_proxy:
                token_abi = contract_abis[TOKEN_ABI_NAME]['abi']
                self.token_proxy = ContractProxy(
                    self.web3, self.privkey, token_address, token_abi, GAS_PRICE, GAS_LIMIT
                )

        assert self.web3
        assert self.channel_manager_proxy
        assert self.token_proxy
        assert self.channel_manager_proxy.web3 == self.web3 == self.token_proxy.web3

        netid = self.web3.version.network
        self.balances_filename = 'balances_{}_{}.json'.format(
            NETWORK_NAMES.get(netid, netid), self.account[:10]
        )

        self.filelock = filelock.FileLock(os.path.join(self.datadir, self.balances_filename))
        self.filelock.acquire(timeout=0)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.filelock.release()

    def open_channel(self, deposit: int, channel_fee: int):
        """
        Attempts to open a new channel with the given deposit. Blocks until the
        creation transaction is found in a pending block or timeout is reached. The new channel is returned.
        """
        assert isinstance(deposit, int)
        assert channel_fee > 0
        assert channel_fee * 3 < deposit
        assert self.channel is None or self.channel.state == Channel.State.closed
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
            channel = Channel(
                self,
                event['args']['_sender'],
                event['blockNumber'],
                event['args']['_deposit'],
                event['args']['_channel_fee'],
                event['args']['_random_n']
            )
            self.channel = channel
        else:
            log.info('Error: No event received.')
            channel = None

        return channel