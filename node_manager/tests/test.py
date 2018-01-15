import json

from web3 import HTTPProvider, Web3

with open('../../data1.json') as data_file:
    data = json.load(data_file)
web3 = Web3(HTTPProvider("http://localhost:8545"))
contract = web3.eth.contract(contract_name='NodeManager', address=data['node_manager_address'],
                             abi=data['node_manager_abi'])
print(str(contract.call().getTime()))