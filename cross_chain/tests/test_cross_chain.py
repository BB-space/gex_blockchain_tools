import threading
from random import randint
from ecdsa import SigningKey, SECP256k1
from scripts.node import Node
from scripts.user import User
from web3 import HTTPProvider
import pytest
import sys
import json
import time
import sha3

sys.path.append('../../gex_chain')
from gex_chain.sign import sha3 as custom_sha3
from populus_utils import *

try:
    from .config import *
except SystemError:
    from config import *


def start_node():
    node = Node()
    print("Node started " + str(int(round(time.time() * 1000))))


def generate_address():
    keccak = sha3.keccak_256()
    priv = SigningKey.generate(curve=SECP256k1)
    pub = priv.get_verifying_key().to_string()
    keccak.update(pub)
    return "0x" + keccak.hexdigest()[24:]


class TestGeneral:
    node_num = 2

    def setup_class(self):
        print("setup_class")
        with open(FILE_PATH) as data_file:
            self.data = json.load(data_file)
        self.user = User()
        nodes = []
        for i in range(0, self.node_num):
            node = threading.Thread(target=start_node, daemon=True)
            node.start()
            nodes.append(node)

    @pytest.mark.parametrize(('block_number', 'addr_from', 'addr_to', 'amount'), [
        (319, generate_address(), generate_address(), 100)])
    def test_sha3(self, block_number, addr_from, addr_to, amount):
        web3 = Web3(HTTPProvider(gex_chain))
        sha3_python = web3.toHex(custom_sha3(block_number, addr_from, addr_to, amount))
        gex_contract = web3.eth.contract(contract_name='GexContract', address=self.data['GexContract'],
                                         abi=self.data['GexContract_abi'])
        sha3_solidity = web3.toHex(gex_contract.call().generateEventID(block_number, addr_from, addr_to, amount))
        assert sha3_python == sha3_solidity

    @pytest.mark.parametrize(('iterations_number', 'nodes_number', 'nodes_needed'), [(50, 40, 10)])
    def test_check_node(self, iterations_number, nodes_number, nodes_needed):
        web3 = Web3(HTTPProvider(gex_chain))
        for i in range(1, iterations_number):
            print("Iteration " + str(i))
            event_id = web3.toHex(
                custom_sha3(randint(0, 100000), generate_address(), generate_address(), randint(0, 100000)))
            count = 0
            for j in range(1, nodes_number):
                new_id = web3.toHex(custom_sha3(generate_address()))
                result = hex(int(event_id, 16) ^ int(new_id, 16))
                num = int(result, 16)
                if num % 10000 > 5000:
                    count += 1
                    if count == nodes_needed:
                        print(j)
                        break

    @pytest.mark.parametrize(('is_gex_net', 'addr_from', 'addr_to', 'amount', 'wait_sec'), [
        (True, gex_address, eth_address, 50, 60), (False, eth_address, gex_address, 50, 60)])
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
