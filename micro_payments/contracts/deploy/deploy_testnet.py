import json
import time
import os
from populus import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
from web3.utils.compat import (
    Timeout,
)
from ecdsa import SigningKey, SECP256k1
import sha3
import sign
import binascii
import random
import unittest
from ethereum.utils import encode_hex
import microraiden.utils as utils
from config import *
try:
    from .config import *
except:
    pass

def check_successful_tx(web3: Web3, txid: str, timeout=180) -> dict:
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)
    assert txinfo['gas'] != receipt['gasUsed']  # why does this work?
    return receipt


def generate_wallets():
    for i in range(SENDERS - 1):
        priv_key, address = create_wallet()
        private_keys.append(priv_key)
        addresses.append('0x' + address)


def create_wallet():
    keccak = sha3.keccak_256()
    priv = SigningKey.generate(curve=SECP256k1)
    pub = priv.get_verifying_key().to_string()
    keccak.update(pub)
    address = keccak.hexdigest()[24:]
    return (encode_hex(priv.to_string()), address)


def write_to_file(**kwargs):
    path = kwargs.pop('file_path', FILE_PATH)
    with open(path, 'w') as data_file:
        json.dump(kwargs, data_file)


def read_from_file():
    with open(FILE_PATH) as data_file:
        data = json.load(data_file)
    return data


def wait(transfer_filter, timeout=30):
    with Timeout(timeout) as timeout:
        while not transfer_filter.get(False):
            timeout.sleep(2)


def deploy_contracts():
    if os.path.isfile(FILE_PATH) and \
                    os.path.getmtime(FILE_PATH) > os.path.getmtime('contracts/RaidenMicroTransferChannels.sol'):
        return

    print('Deploying new contracts')
    project = Project()
    with project.get_chain(CHAIN_NAME) as chain:
        web3 = chain.web3
        owner = web3.eth.accounts[0]

        # token = chain.provider.get_contract_factory('ERC223Token')  # This will be the abi of the token
        # tx_hash = token.deploy(args=[supply, token_name, token_decimals, token_symbol],
        #                       transaction={'from': owner})  # the way we deploy contracts
        # receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        token_address = '0x1cd17fc4a2edc4c0521926166e07a424588ae1cb' # receipt['contractAddress']
        print(token_name, ' address is', token_address)

        channel_factory = chain.provider.get_contract_factory('RaidenMicroTransferChannels')
        tx_hash = channel_factory.deploy(
            args=[token_address, challenge_period, channel_lifetime],
            transaction={'from': owner}
        )
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        channels_address = receipt['contractAddress']
        print('RaidenMicroTransferChannels address is', channels_address)

        # for sender in addresses:
        #     token(token_address).transact({'from': owner}).transfer(sender, token_assign)
        # for sender in sender_addresses:
        #     token(token_address).transact({'from': owner}).transfer(sender, token_assign)

    write_to_file(token_address=token_address, channels_address=channels_address)
    print('Deployed')


def convert_to_256(address, balance):
    return


class TestMTC:

    def set_up(self):
        generate_wallets()
        deploy_contracts()
        self.project = Project()
        with self.project.get_chain(CHAIN_NAME) as chain:
            self.web3 = chain.web3
            self.info = read_from_file()
            self.rand = random.Random()
            self.channel = chain.provider\
                .get_contract_factory('RaidenMicroTransferChannels')(self.info['channels_address'])
            self.token = chain.provider.get_contract_factory('ERC223Token')(self.info['token_address'])
            self.sender = self.web3.eth.accounts[0]
            self.sender_key = utils.get_private_key(signer_key_path, signer_pass_path)
        # print(self.channel.call().createChannelPrivate(self.sender, 555, 1428715233280))

    def test_right_sign(self):
        data = []
        for i in range(SENDERS - 1):
            amount = 5491 * 10 ** 18
            address = int(addresses[i], 0)
            data.append(D160 * amount + address)

        for i in range(SENDERS - 1):
            # with self.subTest(address=addresses[i]):
            balance_msg = self.channel.call().getBalanceMessage(addresses[i], 1, data)
            balance_msg_sig, _ = sign.check(balance_msg, binascii.unhexlify(private_keys[i]))
            ec_recovered_addr = self.channel.call() \
                .verifyBalanceProof(addresses[i], 1, data, balance_msg_sig)
            assert ec_recovered_addr == addresses[i]
        print('signs are right')

    def test_create_channel(self):
        print('Creating channel')
        data_bytes = b'\x00\x00\x00\x00\x10'
        tx_hash = self.token.transact({'from': self.sender}) \
            .transfer(self.info['channels_address'], 1428715233280, data_bytes)
        print(tx_hash)
        receipt = check_successful_tx(self.web3, tx_hash, txn_wait)
        self.open_block = receipt['blockNumber']
        print('Channel should be created, waiting')
        time.sleep(15 * 3)
        tx_hash = self.channel.transact({'from': self.sender}) \
            .registerMaintainer(self.sender, self.open_block)
        receipt = check_successful_tx(self.web3, tx_hash, txn_wait)

        # transfer_filter = self.token.on('Transfer')
        # wait(transfer_filter, event_wait)

        print(self.channel.call().getChannelInfo(self.sender, self.open_block))

    def test_channel_sign(self):
        print('Waiting for channel lifetime to end')
        time.sleep(15 * (channel_lifetime + 1))
        print('Lifetime should have ended')
        data = [convert_to_256(self.web3.eth.accounts[1], 10 * 10 ** token_decimals)]
        balance_msg = self.channel.call().getBalanceMessage(self.sender, self.open_block, data)
        balance_msg_sig, _ = sign.check(balance_msg, binascii.unhexlify(self.sender_key))
        self.channel.transact({'from': self.sender}).close(self.sender, self.open_block, data, balance_msg_sig)
        time.sleep(15 * (5 + 1))
        # close_filter = self.channel.on('ChannelCloseRequested')
        # wait(close_filter, event_wait)

        print(self.channel.call().getChannelInfo(self.sender, self.open_block))


if __name__ == '__main__':
    test = TestMTC()
    test.set_up()
    # test.test_right_sign()
    test.test_create_channel()
    # test.test_channel_sign()

