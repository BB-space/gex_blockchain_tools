import json
from populus import Project
import sys

try:
    from .config import *
except SystemError:
    from config import *

sys.path.append('../../gex_chain')
from populus_utils import *


def write_to_file(**kwargs):
    path = kwargs.pop('file_path', FILE_PATH)
    with open(path, 'w') as data_file:
        json.dump(kwargs, data_file)

def deploy():
    print('Deploying contracts')
    project = Project()
    with project.get_chain(TEST_CHAIN_NAME) as chain:
        web3 = chain.web3
        owner = web3.eth.accounts[0]
        # GEXToken
        GEXToken = chain.provider.get_contract_factory('GEXToken')
        tx_hash = GEXToken.deploy(transaction={'from': owner})
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        gex_token_address = receipt['contractAddress']
        print('GEXToken deployed')
        # Contract
        contract = chain.provider.get_contract_factory('NodeManager')
        tx_hash = contract.deploy(
            args=[gex_token_address, 5000000],
            transaction={'from': owner}
        )
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        contract_address = receipt['contractAddress']
        print('Contract deployed')
        write_to_file(
            token_abi=GEXToken.abi,
            token_address=gex_token_address,
            node_manager_abi=contract.abi,
            node_manager_address=contract_address,
        )
    print('Deployed')

if __name__ == '__main__':
    deploy()
