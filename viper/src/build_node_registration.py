import json
import sys

from web3 import Web3, HTTPProvider

sys.path.append('./Deployer')
from Deployer import Deployer


def write_to_file(contracts_data, file_path):
    with open(file_path, 'w') as data_file:
        json.dump(contracts_data, data_file)


web3 = Web3(HTTPProvider('http://10.1.0.11:8545'))
web3.personal.unlockAccount(web3.eth.accounts[0], '123', 0)
deployer = Deployer('http://10.1.0.11:8545', web3.eth.accounts[0], '123')

TOKEN_NAME = "GexToken"
TOKEN_SYMBOL = "GEX"
TOKEN_DECIMALS = 18
TOKEN_INITIAL_SUPPLY = 1000
TOKEN_TOTAL_SUPPLY = 10000000
token_contract_address, token_contract_abi = deployer.deploy("contracts/gex_token.v.py",
                                                             (TOKEN_NAME, TOKEN_SYMBOL, TOKEN_DECIMALS,
                                                              TOKEN_TOTAL_SUPPLY, TOKEN_INITIAL_SUPPLY))

registration_contract_address, registration_contract_abi = deployer.deploy("contracts/node_registration.v.py",
                                                                           (token_contract_address,))

token = web3.eth.contract(contract_name='Token', address=token_contract_address, abi=token_contract_abi)
deployer.wait_for_transaction(token.transact({'from': web3.eth.accounts[0]}).set_owner(1, registration_contract_address))
print("Added owner to the Token contract")

data = {}
data['token_address'] = token_contract_address
data['token_abi'] = token_contract_abi
data['registration_address'] = registration_contract_address
data['registration_abi'] = registration_contract_abi
write_to_file(data, "../data.json")
print("Done!")
