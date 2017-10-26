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


def deploy_contracts():
    print('Deploying contracts')
    project = Project()
    with project.get_chain(CHAIN_NAME) as chain:
        web3 = chain.web3
        owner = web3.eth.accounts[0]
        print(chain.provider)
        # GEXToken
        gex_token = chain.provider.get_contract_factory('GEXToken')
        tx_hash = gex_token.deploy(transaction={'from': owner})
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        gex_token_address = receipt['contractAddress']
        # ETHToken
        eth_token = chain.provider.get_contract_factory('ETHToken')
        tx_hash = gex_token.deploy(transaction={'from': owner})
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        eth_token_address = receipt['contractAddress']
        # GexContract
        gex_contract = chain.provider.get_contract_factory('MicroTransferChannels')
        tx_hash = gex_contract.deploy(
            args=[gex_token_address],
            transaction={'from': owner}
        )
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        gex_contract_address = receipt['contractAddress']
        # EthContract
        eth_contract = chain.provider.get_contract_factory('MicroTransferChannels')
        tx_hash = eth_contract.deploy(
            args=[eth_token_address],
            transaction={'from': owner}
        )
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        eth_contract_address = receipt['contractAddress']
        # Ownership
        tx_hash = gex_token.transact({'from': owner}).transferOwnership(gex_contract_address)
        check_successful_tx(chain.web3, tx_hash, txn_wait)
        print('GEXToken ownership is established')
        tx_hash = eth_token.transact({'from': owner}).transferOwnership(eth_contract_address)
        check_successful_tx(chain.web3, tx_hash, txn_wait)
        print('ETHToken ownership is established')
        write_to_file(
            EthContract_abi=eth_contract.abi,
            GexContract_abi=gex_contract.abi,
            GEXToken_abi=gex_token.abi,
            ETHToken_abi=eth_token.abi,
            GexContract=gex_contract_address,
            EthContract=eth_contract_address,
            ETHToken=eth_token_address
        )
    print('Deployed')


if __name__ == '__main__':
    deploy_contracts()
