import json
import logging
import os

import filelock
from gex_chain.crypto import privkey_to_addr
from gex_chain.utils import get_private_key, get_data_for_token
from micro_payments.config import GAS_LIMIT, GAS_PRICE, \
    NETWORK_NAMES, APP_FOLDER, DATA_FILE_NAME
from micro_payments.contract_proxy import ContractProxy, ChannelContractProxy
from web3 import Web3
from web3.providers.rpc import RPCProvider


from micro_payments.event_listener.listener import (
    listen_for_balances_change,
    listen_for_channel_closing,
    listen_for_channel_creation,
    listen_for_channel_settle,
    listen_for_channel_top_up,
    listen_for_cheating_report,
    listen_for_maintainer_registration,
    listen_for_topic_creation
)
from micro_payments.channels.sender_channel import SenderChannel
from micro_payments.channels.receiving_channel import ReceivingChannel
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
            node_info_address: str = None,
            rpc: RPCProvider = None,
            web3: Web3 = None,
            channel_manager_proxy: ChannelContractProxy = None,
            token_proxy: ContractProxy = None,
            node_info_proxy: ContractProxy = None,
            rpc_endpoint: str = '127.0.0.1',
            rpc_port: int = 8545,
            data_file_path: str = DATA_FILE_NAME

    ) -> None:
        assert privkey or key_path
        assert not privkey or isinstance(privkey, str)

        # Plain copy initializations.
        self.private_key = privkey
        self.data_dir = APP_FOLDER
        self.channel_manager_address = channel_manager_address
        self.token_address = token_address
        self.web3 = web3
        self.channel_manager_proxy = channel_manager_proxy
        self.token_proxy = token_proxy
        self.node_info_proxy = node_info_proxy

        # Load private key from file if none is specified on command line.
        if not privkey:
            self.private_key = get_private_key(key_path, key_password_path)
            assert self.private_key is not None

        os.makedirs(self.data_dir, exist_ok=True)
        assert os.path.isdir(self.data_dir)

        self.account = privkey_to_addr(self.private_key)
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
        data_file_path = os.path.join(self.data_dir, data_file_path)
        if not channel_manager_proxy or not token_proxy or not node_info_proxy:
            with open(data_file_path) as abi_file:
                data_file = json.load(abi_file)
            if not channel_manager_address:
                channel_manager_address = data_file['channels_address']
            if not token_address:
                token_address = data_file['token_address']
            if not node_info_address:
                node_info_address = data_file['node_info_address']

            if not channel_manager_proxy:
                channel_manager_abi = data_file['channels_abi']
                self.channel_manager_proxy = ChannelContractProxy(
                    self.web3,
                    self.private_key,
                    channel_manager_address,
                    channel_manager_abi,
                    GAS_PRICE,
                    GAS_LIMIT
                )

            if not token_proxy:
                token_abi = data_file['token_abi']
                self.token_proxy = ContractProxy(
                    self.web3, self.private_key, token_address, token_abi, GAS_PRICE, GAS_LIMIT
                )

            if not node_info_proxy:
                node_info_abi = data_file['node_info_abi']
                self.node_info_proxy = ContractProxy(
                    self.web3, self.private_key, node_info_address, node_info_abi, GAS_PRICE, GAS_LIMIT
                )

        assert self.web3
        assert self.channel_manager_proxy
        assert self.token_proxy
        assert self.channel_manager_proxy.web3 == self.web3 == self.token_proxy.web3

        net_id = self.web3.version.network
        self.balances_filename = 'balances_{}_{}.json'.format(
            NETWORK_NAMES.get(net_id, net_id), self.account[:10]
        )

        self.file_lock = filelock.FileLock(os.path.join(self.data_dir, self.balances_filename))
        self.file_lock.acquire(timeout=0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.file_lock.release()

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
            channel.set_topic_event_listener(listen_for_topic_creation(
                self.channel_manager_proxy.contract,
                {'filters': {'_sender': self.account, '_open_block_number': channel.block}},
                channel.topic_created_callback
            ))

        else:
            log.info('Error: No event received.')
            channel = None

        return channel

    def maintain_channel(self, sender: str, open_block: int):
        channel = MaintainerChannel(self, sender, open_block)

        current_block = self.web3.eth.blockNumber
        tx = self.channel_manager_proxy.create_signed_transaction(
            'registerMaintainer', [sender, open_block]
        )

        self.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for MaintainerRegistered event on the blockchain...')
        maintainer_event = self.channel_manager_proxy.get_maintainer_registered_event_blocking(
            sender, open_block, self.account, current_block + 1
        )
        topic_created_event = self.channel_manager_proxy.get_channel_topic_created_logs(
            current_block + 1, filters={
                '_sender': sender,
                '_open_block_number': open_block,
                '_topic_holder': self.account
            }
        )
        if maintainer_event:
            if len(topic_created_event) > 0:
                event = topic_created_event.pop(0)
                # test check
                if event['args']['_topic_holder'] == self.account:
                    log.info('I am the topic_holder of the channel {}, {}'.format(
                        event['args']['_sender'],
                        event['args']['_open_block_number']
                    ))
                    pass
                    # TODO create a topic here!

            self.maintaining_channels.append(channel)
            channel.create_receiving_kafka()
            channel.config_and_start_kafka()
            channel.set
            # TODO register event listeners

            return channel
        else:
            log.error('No event received')
            return None

    def get_receiving_channel(self, sender):
        current_block = self.web3.eth.blockNumber

        log.info('Waiting for channel creation event on the blockchain...')
        event = self.channel_manager_proxy.get_channel_created_event_blocking(
            sender, current_block + 1
        )

        if event:
            log.info('Event received. Channel was created in block {}.'.format(event['blockNumber']))
            channel = ReceivingChannel(
                self,
                event['args']['_sender'],
                event['blockNumber'],
                event['args']['_deposit'],
                event['args']['_channel_fee'],
                event['args']['_random_n']
            )
            self.receiving_channels.append(channel)
            # TODO add a listener and listen for a topic created event to create a receiving_kafka
        else:
            log.info('Error: No event received.')
            channel = None

        return channel

    def add_receiving_channel(self, sender, open_block):
        try:
            channel_info = self.channel_manager_proxy.contract.call().getChannelInfo(sender, open_block)
        except ValueError:  # TODO check what error is actually raised
            log.error('Channel for sender {} and block {} was not yet created or no maintainers registered'.format(
                sender, open_block
            ))
            return None
        channel = ReceivingChannel(self, sender, open_block, channel_info[1], channel_info[3], topic_holder=channel_info[4])
        channel.create_receiving_kafka()
        channel.config_and_start_kafka()
        # TODO add a listener and listen
        self.receiving_channels.append(channel)
        return channel

    def get_node_ip(self, node_address):
        return self.node_info_proxy.contract.call().getIp(node_address)  # TODO test
