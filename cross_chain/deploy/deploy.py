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


def deploy_test():
    print('Deploying contracts')
    project = Project()
    with project.get_chain(LOCAL_CHAIN_NAME) as chain:
        web3 = chain.web3
        owner = web3.eth.accounts[0]
        test = chain.provider.get_contract_factory('Test')
        tx_hash = test.deploy(transaction={'from': owner})
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        test_address = receipt['contractAddress']
        print('Test deployed')
        write_to_file(
            Test_abi=test.abi,
            Test=test_address
        )
    print('Deployed')


def deploy_remote():
    print('Remote deploy')
    deploy(LOCAL_CHAIN_NAME, REMOTE_CHAIN_NAME)


def deploy_local():
    print('Local deploy')
    deploy(LOCAL_CHAIN_NAME, LOCAL_CHAIN_NAME)


def deploy(gex_chain_name, eth_chain_name):
    print('Deploying contracts')
    project = Project()
    with project.get_chain(gex_chain_name) as gex_chain, project.get_chain(eth_chain_name) as eth_chain:
        gex_web3 = gex_chain.web3
        eth_web3 = eth_chain.web3
        # todo change address
        gex_owner = gex_web3.eth.accounts[0]
        eth_owner = eth_web3.eth.accounts[0]
        # GEXToken
        GEXToken = gex_chain.provider.get_contract_factory('GEXToken')
        tx_hash = GEXToken.deploy(transaction={'from': gex_owner})
        receipt = check_successful_tx(gex_chain.web3, tx_hash, txn_wait)
        gex_token_address = receipt['contractAddress']
        print('GEXToken deployed')
        # ETHToken
        ETHToken = eth_chain.provider.get_contract_factory('ETHToken')
        tx_hash = ETHToken.deploy(transaction={'from': eth_owner})
        receipt = check_successful_tx(eth_chain.web3, tx_hash, txn_wait)
        eth_token_address = receipt['contractAddress']
        print('ETHToken deployed')
        # GexContract
        GEXContract = gex_chain.provider.get_contract_factory('GexContract')
        tx_hash = GEXContract.deploy(
            args=[gex_token_address],
            transaction={'from': gex_owner}
        )
        receipt = check_successful_tx(gex_chain.web3, tx_hash, txn_wait)
        gex_contract_address = receipt['contractAddress']
        print('GexContract deployed')
        # EthContract
        ETHContract = eth_chain.provider.get_contract_factory('EthContract')
        tx_hash = ETHContract.deploy(
            args=[eth_token_address],
            transaction={'from': eth_owner}
        )
        receipt = check_successful_tx(eth_chain.web3, tx_hash, txn_wait)
        eth_contract_address = receipt['contractAddress']
        print('EthContract deployed')
        # Ownership
        gex_token = GEXToken(gex_token_address)
        tx_hash = gex_token.transact({'from': gex_owner}).transferOwnership(gex_contract_address)
        check_successful_tx(gex_chain.web3, tx_hash, txn_wait)
        print('GEXToken ownership is established')
        eth_token = ETHToken(eth_token_address)
        tx_hash = eth_token.transact({'from': eth_owner}).transferOwnership(eth_contract_address)
        check_successful_tx(eth_chain.web3, tx_hash, txn_wait)
        print('ETHToken ownership is established')
        write_to_file(
            EthContract_abi=ETHContract.abi,
            GexContract_abi=GEXContract.abi,
            GEXToken_abi=GEXToken.abi,
            ETHToken_abi=ETHToken.abi,
            GexContract=gex_contract_address,
            EthContract=eth_contract_address,
            ETHToken=eth_token_address,
            GEXToken=gex_token_address,
        )
    print('Deployed')


if __name__ == '__main__':
    #deploy_remote()
    #deploy_local()
    deploy_test()
