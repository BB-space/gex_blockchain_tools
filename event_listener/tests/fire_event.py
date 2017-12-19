from web3 import Web3, HTTPProvider
import json
from random import randrange

with open('../viper/data.json') as data_file:
    contract_data = json.load(data_file)

web3 = Web3(HTTPProvider('http://localhost:8545'))

contract = web3.eth.contract(contract_name='TestContract', address=contract_data['registration_address'],
                             abi=contract_data['registration_abi'])

print(contract.transact({'from': web3.eth.accounts[0]}).setNumber(randrange(0, 100)))
