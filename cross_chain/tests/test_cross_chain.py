from web3 import Web3, HTTPProvider
import pytest
import sys
import json

sys.path.append('../../gex_chain')
from gex_chain.sign import sha3
from populus_utils import *

try:
    from .config import *
except SystemError:
    from config import *


class GeneralTests:
    def __init__(self):
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
