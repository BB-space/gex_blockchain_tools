import logging
import threading

import datetime
from scripts.node import Node
from scripts.user import User
from web3 import Web3, HTTPProvider
import pytest
import sys
import json
import time

sys.path.append('../../gex_chain')
from gex_chain.sign import sha3
from populus_utils import *

try:
    from .config import *
except SystemError:
    from config import *


class TestGeneral:
    def setup(self):
        with open(FILE_PATH) as data_file:
            self.data = json.load(data_file)

    @pytest.mark.parametrize(('block_number', 'addr_from', 'addr_to', 'amount'), [
        (319, "0xd88f5b60ab616a56db76ed893cde448daae00de8", "0x82c32dd183c659eb0f484d95f6e43989ddc53734", 100)])
    def test_sha3(self, block_number, addr_from, addr_to, amount):
        web3 = Web3(HTTPProvider(chain))

        sha3_python = web3.toHex(sha3(block_number, addr_from, addr_to, amount))
        gex_contract = web3.eth.contract(contract_name='GexContract', address=self.data['GexContract'],
                                         abi=self.data['GexContract_abi'])
        sha3_solidity = web3.toHex(gex_contract.call().generateEventID(block_number, addr_from, addr_to, amount))
        assert sha3_python == sha3_solidity

    def start_node(self):
        node = Node()
        print("Node started " + str(int(round(time.time() * 1000))))
        # while True:
        #    pass

    @pytest.mark.parametrize(('node_num', 'addr_from', 'addr_to', 'amount', 'wait_sec'), [
        (2, "0xd88f5b60ab616a56db76ed893cde448daae00de8", "0x82c32dd183c659eb0f484d95f6e43989ddc53734", 100, 60)])
    def test_workflow(self, node_num, addr_from, addr_to, amount, wait_sec):
        web3 = Web3(HTTPProvider(chain))
        gex_token = web3.eth.contract(contract_name='GEXToken', address=self.data['GEXToken'],
                                      abi=self.data['GEXToken_abi'])
        eth_token = web3.eth.contract(contract_name='ETHToken', address=self.data['ETHToken'],
                                      abi=self.data['ETHToken_abi'])
        user = User()
        nodes = []
        for i in range(0, node_num):
            node = threading.Thread(target=self.start_node, daemon=True)
            node.start()
            node.join()
            nodes.append(node)
        print(amount)
        balance_from_before = gex_token.call().balanceOf(addr_from)
        balance_to_before = eth_token.call().balanceOf(addr_to)
        print(str(balance_from_before) + " " + str(balance_to_before))
        user.create_transfer(True, addr_from, addr_to, amount)
        time.sleep(wait_sec)
        balance_from_after = gex_token.call().balanceOf(addr_from)
        balance_to_after = eth_token.call().balanceOf(addr_to)
        print(str(balance_from_after) + " " + str(balance_to_after))
        assert balance_from_after == balance_from_before - amount
        assert balance_to_after == balance_to_before + amount
