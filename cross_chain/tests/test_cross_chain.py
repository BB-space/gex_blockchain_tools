import threading
import multiprocessing
from scripts.node import Node
from scripts.user import User
from web3 import HTTPProvider
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


def start_node():
    node = Node()
    print("Node started " + str(int(round(time.time() * 1000))))


class TestGeneral:
    node_num = 2

    def setup_class(self):
        print("setup_class")
        with open(FILE_PATH) as data_file:
            self.data = json.load(data_file)
        self.user = User()
        nodes = []
        # stop_event = threading.Event()
        for i in range(0, self.node_num):
            # todo pool
            # node = multiprocessing.Process(target=self.start_node)
            node = threading.Thread(target=start_node, daemon=True)
            node.start()
            # node.join()
            nodes.append(node)

    @pytest.mark.parametrize(('block_number', 'addr_from', 'addr_to', 'amount'), [
        (319, "0xd88f5b60ab616a56db76ed893cde448daae00de8", "0x82c32dd183c659eb0f484d95f6e43989ddc53734", 100)])
    def test_sha3(self, block_number, addr_from, addr_to, amount):
        web3 = Web3(HTTPProvider(gex_chain))

        sha3_python = web3.toHex(sha3(block_number, addr_from, addr_to, amount))
        gex_contract = web3.eth.contract(contract_name='GexContract', address=self.data['GexContract'],
                                         abi=self.data['GexContract_abi'])
        sha3_solidity = web3.toHex(gex_contract.call().generateEventID(block_number, addr_from, addr_to, amount))
        assert sha3_python == sha3_solidity

    def xor_strings(self, xs, ys):
        return "".join(chr(ord(x) ^ ord(y)) for x, y in zip(xs, ys))

    @pytest.mark.parametrize(('block_number', 'addr_from', 'addr_to', 'amount', 'node_addr'), [
        (319, "0x1fcfd3afe7f20efb2f8b6ca53a411e2447004313", "0x65bdc28b5c50f31cb06a4b0ffa6511cd3d7b1662", 100,
         "0x12d959f34cab3d5db2559403ab474e1c1af143f8"),
        (319, "0x1fcfd3afe7f20efb2f8b6ca53a411e2447004313", "0x65bdc28b5c50f31cb06a4b0ffa6511cd3d7b1662", 100,
         "0xb4b6ce377ce9ac66e84417b2a463f45e49262b0d"),
        (319, "0x1fcfd3afe7f20efb2f8b6ca53a411e2447004313", "0x65bdc28b5c50f31cb06a4b0ffa6511cd3d7b1662", 100,
         "0xd88f5b60ab616a56db76ed893cde448daae00de8")
    ])
    def test_check_node(self, block_number, addr_from, addr_to, amount, node_addr):
        web3 = Web3(HTTPProvider(gex_chain))
        event_id = web3.toHex(sha3(block_number, addr_from, addr_to, amount))
        print(event_id)
        new_block_number = web3.eth.blockNumber
        new_id = web3.toHex(sha3(new_block_number, node_addr))
        print(new_id)
        result = hex(int(event_id, 16) ^ int(new_id, 16))
        print(int(result, 16))
        print(result)


'''
    # remote "0x1fcfd3afe7f20efb2f8b6ca53a411e2447004313" "0x65bdc28b5c50f31cb06a4b0ffa6511cd3d7b1662"
    # local  "0xb4b6ce377ce9ac66e84417b2a463f45e49262b0d" "0x12d959f34cab3d5db2559403ab474e1c1af143f8"
    @pytest.mark.parametrize(('is_gex_net', 'addr_from', 'addr_to', 'amount', 'wait_sec'), [
        (True, "0xb4b6ce377ce9ac66e84417b2a463f45e49262b0d", "0x65bdc28b5c50f31cb06a4b0ffa6511cd3d7b1662", 50, 60),
        (False, "0x1fcfd3afe7f20efb2f8b6ca53a411e2447004313", "0x12d959f34cab3d5db2559403ab474e1c1af143f8", 50, 60)])
    def test_workflow(self, is_gex_net, addr_from, addr_to, amount, wait_sec):
        gex_web3 = Web3(HTTPProvider(gex_chain))
        eth_web3 = Web3(HTTPProvider(eth_chain))
        if is_gex_net:
            burn_token = gex_web3.eth.contract(contract_name='GEXToken', address=self.data['GEXToken'],
                                           abi=self.data['GEXToken_abi'])
            mint_token = eth_web3.eth.contract(contract_name='ETHToken', address=self.data['ETHToken'],
                                           abi=self.data['ETHToken_abi'])
        else:
            mint_token = gex_web3.eth.contract(contract_name='GEXToken', address=self.data['GEXToken'],
                                           abi=self.data['GEXToken_abi'])
            burn_token = eth_web3.eth.contract(contract_name='ETHToken', address=self.data['ETHToken'],
                                           abi=self.data['ETHToken_abi'])
        balance_from_before = burn_token.call().balanceOf(addr_from)
        balance_to_before = mint_token.call().balanceOf(addr_to)
        print(str(balance_from_before) + " " + str(balance_to_before))
        self.user.create_transfer(is_gex_net, addr_from, addr_to, amount)
        time.sleep(wait_sec)
        balance_from_after = burn_token.call().balanceOf(addr_from)
        balance_to_after = mint_token.call().balanceOf(addr_to)
        print(str(balance_from_after) + " " + str(balance_to_after))
        assert balance_from_after == balance_from_before - amount
        assert balance_to_after == balance_to_before + amount
'''
