import json
import time

from web3 import HTTPProvider, Web3


def approval_callback(result):
    print("Approval. owner: " + result['args']['_owner'] + " spender: " + result['args']['_spender'] + " value: " + str(
        result['args']['_value']))


def node_created_callback(result):
    print("Node Created. nodeID: " + str(result['args']['node_id']) + " nodeIP: " + result['args'][
        'node_ip'] + " user_port: " + str(
        result['args']['user_port']) + " cluster_port: " + str(result['args']['cluster_port']))


with open('../data.json') as data_file:
    data = json.load(data_file)
web3 = Web3(HTTPProvider('http://localhost:8545'))
token = web3.eth.contract(contract_name='Token', address=data['token_address'], abi=data['token_abi'])
approval = token.on('Approval')
approval.watch(approval_callback)
contract = web3.eth.contract(contract_name='Registration', address=data['registration_address'],
                             abi=data['registration_abi'])

node_created = contract.on('NodeCreated')
node_created.watch(node_created_callback)

print(
    str(token.call().balanceOf(web3.eth.accounts[0])) + " " + str(token.call().balanceOf(data['registration_address'])))
token.transact({'from': web3.eth.accounts[0]}).approve(data['registration_address'], 200)
time.sleep(25)
contract.transact({'from': web3.eth.accounts[0]}).deposit(web3.eth.accounts[0], 200, "10.11.0.1", 3333, 4444)
time.sleep(25)
print(
    str(token.call().balanceOf(web3.eth.accounts[0])) + " " + str(token.call().balanceOf(data['registration_address'])))
print(str(contract.call().getNodeStatus(1)))