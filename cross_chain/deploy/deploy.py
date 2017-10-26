import json
from populus import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
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


def write_to_file(**kwargs):
    path = kwargs.pop('file_path', FILE_PATH)
    with open(path, 'w') as data_file:
        json.dump(kwargs, data_file)


def deploy_test():
    print('Deploying contracts')
    project = Project()
    with project.get_chain(CHAIN_NAME) as chain:
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

def deploy_contracts():
    print('Deploying contracts')
    project = Project()
    with project.get_chain(CHAIN_NAME) as chain:
        web3 = chain.web3
        owner = web3.eth.accounts[0]
        # GEXToken
        GEXToken = chain.provider.get_contract_factory('GEXToken')
        tx_hash = GEXToken.deploy(transaction={'from': owner})
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        gex_token_address = receipt['contractAddress']
        print('GEXToken deployed')
        # ETHToken
        ETHToken = chain.provider.get_contract_factory('ETHToken')
        tx_hash = GEXToken.deploy(transaction={'from': owner})
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        eth_token_address = receipt['contractAddress']
        print('ETHToken deployed')
        # GexContract
        GEXContract = chain.provider.get_contract_factory('GexContract')
        tx_hash = GEXContract.deploy(
            args=[gex_token_address],
            transaction={'from': owner}
        )
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        gex_contract_address = receipt['contractAddress']
        print('GexContract deployed')
        # EthContract
        ETHContract = chain.provider.get_contract_factory('EthContract')
        tx_hash = ETHContract.deploy(
            args=[eth_token_address],
            transaction={'from': owner}
        )
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        eth_contract_address = receipt['contractAddress']
        print('EthContract deployed')
        # Ownership
        gex_token = chain.provider.get_contract_factory('GEXToken')(gex_token_address)
        #gex_token = GEXToken(gex_token_address)
        tx_hash = gex_token.transact({'from': owner}).transferOwnership(gex_contract_address)
        check_successful_tx(chain.web3, tx_hash, txn_wait)
        print('GEXToken ownership is established')
        eth_token = chain.provider.get_contract_factory('ETHToken')(eth_token_address)
        #eth_token = GEXToken(gex_token_address)
        tx_hash = eth_token.transact({'from': owner}).transferOwnership(eth_contract_address)
        check_successful_tx(chain.web3, tx_hash, txn_wait)
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
    deploy_contracts()
    #deploy_test()
