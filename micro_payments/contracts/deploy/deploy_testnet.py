import sys
import json
import time
from threading import Thread
import os
import logging
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
    # assert txinfo['gas'] != receipt['gasUsed']  # why does this work?
    return receipt


def generate_wallets():
    for i in range(SENDERS - 1):
        priv_key, address = create_wallet()
        private_keys.append(priv_key)
        addresses.append('0x'+ address)


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

    # logging.info('Deploying new contracts')
    project = Project()
    with project.get_chain(CHAIN_NAME) as chain:
        web3 = chain.web3
        owner = web3.eth.accounts[0]

        # token = chain.provider.get_contract_factory('ERC223Token')  # This will be the abi of the token
        # tx_hash = token.deploy(args=[supply, token_name, token_decimals, token_symbol],
        #                       transaction={'from': owner})  # the way we deploy contracts
        # receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        token_address = '0x1cd17fc4a2edc4c0521926166e07a424588ae1cb'# receipt['contractAddress']
        # logging.info('{} address is {}'.format(token_name, token_address))

        channel_factory = chain.provider.get_contract_factory('RaidenMicroTransferChannels')
        tx_hash = channel_factory.deploy(
            args=[token_address, challenge_period, channel_lifetime],
            transaction={'from': owner}
        )
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        channels_address = receipt['contractAddress']
        # logging.info('RaidenMicroTransferChannels address is {}'.format(channels_address))

        # for sender in addresses:
        #     token(token_address).transact({'from': owner}).transfer(sender, token_assign)
        # for sender in sender_addresses:
        #     token(token_address).transact({'from': owner}).transfer(sender, token_assign)

    write_to_file(token_address=token_address, channels_address=channels_address)
    print('Deployed')


def generate_data(amounts):
    data = []
    for i in range(len(amounts)):
        data.append(D160 * amounts[i] + int(addresses[i], 0))
    return data


class TestMTC():

    def __init__(self, name):
        self.name = name

    def set_up(self):
        self.logger = logging.getLogger(self.name)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(name)-13s %(levelname)-8s %(message)s'))
        self.logger.addHandler(handler)
        self.project = Project()
        self.open_block = None
        self.key = None
        with self.project.get_chain(CHAIN_NAME) as chain:
            self.web3 = chain.web3
            self.project_info = read_from_file()
            self.rand = random.Random()
            self.channel = chain.provider\
                .get_contract_factory('RaidenMicroTransferChannels')(self.project_info['channels_address'])
            self.token = chain.provider.get_contract_factory('ERC223Token')(self.project_info['token_address'])
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
        self.logger.info('Signs are right')

    def test_create_channel(self):
        self.logger.info('Creating channel')
        data_bytes = b'\x00\x00\x00\x00\x10'
        tx_hash = self.token.transact({'from': self.sender}) \
            .transfer(self.project_info['channels_address'], 1428715233280, data_bytes)
        # print(tx_hash)
        receipt = check_successful_tx(self.web3, tx_hash, txn_wait)
        self.open_block = receipt['blockNumber']
        self.logger.info('Channel should be created')
        tx_hash = self.channel.transact({'from': self.sender}) \
            .registerMaintainer(self.sender, self.open_block)
        check_successful_tx(self.web3, tx_hash, txn_wait)
        info = self.channel.call().getChannelInfo(self.sender, self.open_block)
        self.key = info[0]
        # print(info)

    def test_close_channel(self):
        self.logger.info('Waiting for channel lifetime to end')
        time.sleep(15 * (channel_lifetime + 1))
        self.logger.info('Lifetime should have ended')
        data = []
        amount = 1428715
        address = int(addresses[1], 0)
        data.append(D160 * amount + address)
        balance_msg = self.channel.call().getBalanceMessage(self.sender, self.open_block, data)
        balance_msg_sig, _ = sign.check(balance_msg, binascii.unhexlify(self.sender_key[2:]))
        try:
            self.logger.info(self.channel.call({'from': self.sender}).close(self.sender, self.open_block, data, balance_msg_sig))
        except:
            self.logger.warning('CLOSE REQUEST WILL FAIL')
        tx_hash = self.channel.transact({'from': self.sender}).close(self.sender, self.open_block, data, balance_msg_sig)
        check_successful_tx(self.web3, tx_hash, txn_wait)
        self.logger.info('BLOCK {}'.format(self.open_block))  # TODO write this to the data.json as well?
        try:
            self.logger.info('Channel info: {}'.format(self.channel.call().getChannelInfo(self.sender, self.open_block)))
        except:
            self.logger.warning('Channel info failed in close ×')
        try:
            self.logger.info('Closing request: {}'.format(self.channel.call().getClosingRequestInfo(self.sender, self.open_block)))
        except:
            self.logger.warning('Closing request info failed in close ×')

    def test_send_new_transaction(self):
        data = []
        amount = 1528715
        address = int(addresses[1], 0)
        data.append(D160 * amount + address)
        balance_msg = self.channel.call().getBalanceMessage(self.sender, self.open_block, data)
        balance_msg_sig, _ = sign.check(balance_msg, binascii.unhexlify(self.sender_key[2:]))
        tx_hash = self.channel.transact({'from': self.sender}).submitLaterTransaction(self.sender, self.open_block, data, balance_msg_sig)
        check_successful_tx(self.web3, tx_hash, txn_wait)
        try:
            self.logger.info('Closing request: {}'.format(self.channel.call().getClosingRequestInfo(self.sender, self.open_block)))
        except:
            self.logger.warning('Closing request info failed in send_new_transaction ×')

    def test_settle_channel(self):
        # self.block = ''
        self.logger.info('Waiting for channel settlement to end')
        time.sleep(15 * (challenge_period + 3))
        self.logger.info('Lifetime should have ended')
        tx_hash = self.channel.transact({'from': self.sender}).settle(self.sender, self.open_block)
        try:
            self.logger.info(self.channel.call({'from': self.sender}).settle(self.sender, self.open_block))
        except:
            self.logger.warning('SETTLEMENT FAILED ×')
        check_successful_tx(self.web3, tx_hash, txn_wait)
        try:
            self.logger.warning('Channel info: {}'.format(self.channel.call().getChannelInfo(self.sender, self.open_block)))
        except:
            self.logger.info('Channel info failed in settle ✓')
        try:
            self.logger.warning('Closing request: {}'.format(self.channel.call().getClosingRequestInfo(self.sender, self.open_block)))
        except:
            self.logger.info('Closing request info failed is settle ✓')
        try:
            self.logger.info('Balance: {}'.format(self.channel.call({'from': addresses[1]}).checkBalance()))
        except:
            self.logger.warning('Balance failed in settle ×')

    def test_overspend(self):
        self.set_up()
        self.test_create_channel()
        self.get_all_events()
        data = []
        amount = 142871500000000000  # obviously much more that we've sent initially
        address = int(addresses[1], 0)
        data.append(D160 * amount + address)

        # Trying to close the channel with an overspend
        balance_msg = self.channel.call().getBalanceMessage(self.sender, self.open_block, data)
        balance_msg_sig, _ = sign.check(balance_msg, binascii.unhexlify(self.sender_key[2:]))
        tx_hash = self.channel.transact({'from': self.sender}).close(self.sender, self.open_block, data, balance_msg_sig)
        check_successful_tx(self.web3, tx_hash, txn_wait)
        try:
            self.logger.info('Channel info: {}'.format(self.channel.call().getChannelInfo(self.sender, self.open_block)))
        except:
            self.logger.warning('Channel info failed in overspend. ×')
        try:
            self.logger.warning('Closing request: {}'.format(self.channel.call().getClosingRequestInfo(self.sender, self.open_block)))
        except:
            self.logger.info('Closing request info failed in overspend. ✓')

        # Checking if we've overspent
        self.logger.info(self.channel.call({'from': self.sender}).checkOverspend(self.key, data))

        # Reporting cheating
        right_data = []
        amount = 1428715
        address = int(addresses[1], 0)
        right_data.append(D160 * amount + address)
        right_balance_msg = self.channel.call().getBalanceMessage(self.sender, self.open_block, right_data)
        right_balance_msg_sig, _ = sign.check(right_balance_msg, binascii.unhexlify(self.sender_key[2:]))
        tx_hash = self.channel.transact({'from': self.web3.eth.accounts[1]}).reportCheating(
            self.sender,
            self.open_block,
            right_data,
            right_balance_msg_sig,
            data,
            balance_msg_sig)
        check_successful_tx(self.web3, tx_hash, txn_wait)
        try:
            self.logger.info('Closing request: {}'.format(self.channel.call().getClosingRequestInfo(self.sender, self.open_block)))
        except:
            self.logger.warning('Closing request info failed in close. ×')

    def cheating_template(self, case_n, good_data, bad_data):
        self.set_up()
        self.test_create_channel()
        self.logger.info('Case#: {}, Good data: {}'.format(case_n, good_data))
        bad_balance_msg = self.channel.call().getBalanceMessage(self.sender, self.open_block, bad_data)
        bad_balance_msg_sig, _ = sign.check(bad_balance_msg, binascii.unhexlify(self.sender_key[2:]))
        right_balance_msg = self.channel.call().getBalanceMessage(self.sender, self.open_block, good_data)
        right_balance_msg_sig, _ = sign.check(right_balance_msg, binascii.unhexlify(self.sender_key[2:]))
        tx_hash = self.channel.transact({'from': self.web3.eth.accounts[1]}).reportCheating(
            self.sender,
            self.open_block,
            good_data,
            right_balance_msg_sig,
            bad_data,
            bad_balance_msg_sig)
        check_successful_tx(self.web3, tx_hash, txn_wait)
        try:
            self.logger.info('Closing request: {}'.format(self.channel.call().getClosingRequestInfo(self.sender, self.open_block)))
        except:
            self.logger.warning('Closing request info failed in cheating {}. ×'.format(case_n))

    def test_cheating1(self):
        good_data = generate_data([1428726, 1428726])
        bad_data = generate_data([1428715, 1428715, 1428715])
        self.cheating_template(1, good_data, bad_data)

    def test_cheating2(self):
        good_data = generate_data([1428726, 1428726, 1428726])
        bad_data = generate_data([1428726, 1428725, 1428727])
        self.cheating_template(2, good_data, bad_data)

    def test_cheating3(self):
        good_data = generate_data([1428715, 1428715, 1428715])
        bad_data = generate_data([1428726, 1428726])
        self.cheating_template(3, good_data, bad_data)

    def test_ten_payee_close(self):
        self.set_up()
        self.get_all_events()
        self.test_create_channel()
        self.logger.info('Waiting for channel lifetime to end')
        time.sleep(15 * (channel_lifetime + 1))
        self.logger.info('Lifetime should have ended')
        data = generate_data([1000]*10)
        balance_msg = self.channel.call().getBalanceMessage(self.sender, self.open_block, data)
        balance_msg_sig, _ = sign.check(balance_msg, binascii.unhexlify(self.sender_key[2:]))
        try:
            self.logger.info(
                self.channel.call({'from': self.sender}).close(self.sender, self.open_block, data, balance_msg_sig))
        except:
            self.logger.warning('CLOSE REQUEST WILL FAIL')
        tx_hash = self.channel.transact({'from': self.sender}).close(self.sender, self.open_block, data,
                                                                     balance_msg_sig)
        check_successful_tx(self.web3, tx_hash, txn_wait)
        self.logger.info('BLOCK {}'.format(self.open_block))  # TODO write this to the data.json as well?
        try:
            self.logger.info(
                'Channel info: {}'.format(self.channel.call().getChannelInfo(self.sender, self.open_block)))
        except:
            self.logger.warning('Channel info failed in close ×')
        try:
            self.logger.info(
                'Closing request: {}'.format(self.channel.call().getClosingRequestInfo(self.sender, self.open_block)))
        except:
            self.logger.warning('Closing request info failed in close ×')
        self.test_settle_channel()

    def simple_cycle(self):
        self.set_up()
        self.get_all_events()
        self.test_right_sign()
        self.test_create_channel()
        self.test_close_channel()
        self.test_send_new_transaction()
        self.test_settle_channel()


    def get_all_events(self):
        names = [
            # 'ChannelCreated',
            # 'ChannelToppedUp',
            'ChannelCloseRequested',
            'ChannelSettled',
            # 'MaintainerRegistered',
            # 'ChannelTopicCreated',
            # 'CollateralPayed',
            # 'ClosingBalancesChanged',
            'GasCost']
        for i in names:
            event_filter = self.channel.on(i)
            event_filter.watch(lambda x: self.logger.info(
                'Event: {}, Transaction: {}, Args: {}'.format(x['event'], x['transactionHash'], x['args'])))

if __name__ == '__main__':
    generate_wallets()
    # deploy_contracts()
    threads = [Thread(name='Simple_Cycle', target=TestMTC('Simple_Cycle').test_ten_payee_close)]#,
               # Thread(name='Overspend', target=TestMTC('Overspend').test_overspend),
               # Thread(name='Cheating1', target=TestMTC('Cheating1').test_cheating1),
               # Thread(name='Cheating2', target=TestMTC('Cheating2').test_cheating2),
               # Thread(name='Cheating3', target=TestMTC('Cheating3').test_cheating3)]
    for thread in threads:
        thread.start()
        time.sleep(25)

    for thread in threads:
        thread.join()
