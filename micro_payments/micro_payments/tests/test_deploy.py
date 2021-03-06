import sys
import json
import time
from threading import Thread
import os
import logging
from populus import Project

import sign
import binascii
import random
import microraiden.utils as utils
from gex_chain.populus_utils import check_successful_tx
from micro_payments.deploy.utils import read_from_file, generate_data, generate_wallets
from micro_payments.deploy.config import CHAIN_NAME, signer_key_path, signer_pass_path,\
    addresses, SENDERS, D160, private_keys, txn_wait, channel_lifetime, challenge_period


class TestMTC:
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
                .get_contract_factory('MicroTransferChannels')(self.project_info['channels_address'])
            self.token = chain.provider.get_contract_factory('GEXToken')(self.project_info['token_address'])
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
        self.logger.info(info)

    def test_close_channel(self):
        self.logger.info('Waiting for channel lifetime to end')
        time.sleep(15 * (channel_lifetime + 1))
        self.logger.info('Lifetime should have ended')
        data = []
        amount = 1428715
        address = int(self.web3.eth.accounts[1], 0)
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
        address = int(self.web3.eth.accounts[1], 0)
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

    def test_ten_cheating(self):
        good_data = generate_data([1428726]*10)
        bad_data = generate_data([1428726]*4 + [1428724] + [1428727] + [1428726]*3)
        self.cheating_template(2, good_data, bad_data)

    def simple_cycle(self):
        self.set_up()
        self.get_all_events()
        self.test_right_sign()
        self.test_create_channel()
        self.test_top_up()
        self.test_close_channel()
        self.test_send_new_transaction()
        self.test_settle_channel()
        self.test_withdraw()

    def test_top_up(self):
        data_bytes = b'\x01\x00\x00\x00\x00'
        data_int = int.from_bytes(data_bytes, byteorder='big') + self.open_block
        data_bytes = (data_int).to_bytes(5, byteorder='big')
        assert len(data_bytes) == 5
        tx_hash = self.token.transact({'from': self.sender}) \
            .transfer(self.project_info['channels_address'], 1428715233280, data_bytes)
        receipt = check_successful_tx(self.web3, tx_hash, txn_wait)
        self.logger.info('Channel should be topped up')
        info = self.channel.call().getChannelInfo(self.sender, self.open_block)
        self.key = info[0]
        self.logger.info(info)

    def test_withdraw(self):
        self.logger.info('Balance before: {}'.format(
            self.token.call({'from': self.web3.eth.accounts[1]}).balanceOf(self.web3.eth.accounts[1])))
        tx_hash = self.channel.transact({'from': self.web3.eth.accounts[1]}).withdraw()
        check_successful_tx(self.web3, tx_hash, txn_wait)
        self.logger.info('Balance after: {}'.format(
            self.token.call({'from': self.web3.eth.accounts[1]}).balanceOf(self.web3.eth.accounts[1])))

    def get_all_events(self):
        names = [
            'ChannelCreated',
            'ChannelToppedUp',
            'ChannelCloseRequested',
            'ChannelSettled',
            'MaintainerRegistered',
            'ChannelTopicCreated',
            'CollateralPayed',
            'ClosingBalancesChanged',
        ]
        for i in names:
            event_filter = self.channel.on(i)
            event_filter.watch(lambda x: self.logger.info(
                'Event: {}, Transaction: {}, Args: {}'.format(x['event'], x['transactionHash'], x['args'])))


def run_all_tests():
    generate_wallets()
    threads = [Thread(name='Simple_Cycle', target=TestMTC('Simple_Cycle').simple_cycle),
               Thread(name='Overspend', target=TestMTC('Overspend').test_overspend),
               Thread(name='Cheating1', target=TestMTC('Cheating1').test_cheating1),
               Thread(name='Cheating2', target=TestMTC('Cheating2').test_cheating2),
               Thread(name='Cheating3', target=TestMTC('Cheating3').test_cheating3),
               Thread(name='Ten_Payees', target=TestMTC('Ten_Payees').test_ten_payee_close),
               Thread(name='Ten_Cheating', target=TestMTC('Ten_Cheating').test_ten_cheating)]

    for thread in threads:
        thread.start()
        time.sleep(25)

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    run_all_tests()