import json
import time

from web3 import HTTPProvider, Web3


def approval_callback(result):
    print("Approval. owner: " + result['args']['_owner'] + " spender: " + result['args']['_spender'] + " value: " + str(
        result['args']['_value']))


def node_created_callback(result):
    print("Node Created. nodeID: " + str(result['args']['node_id']) + " nodeIP: " + result['args'][
        'node_ip'] + " port: " + str(result['args']['port']))


def basic_channel_created_callback(result):
    print("Basic channel created. channelID: " + str(result['args']['channel_id']) + " owner: " + result['args'][
        'owner'] + " storage bytes: " + str(result['args']['storage_bytes']) + " lifetime: " + str(
        result['args']['lifetime']) + " number of nodes: " + str(result['args']['number_of_nodes']))


def aggregation_channel_created_callback(result):
    print("Aggregation channel created. channelID: " + str(result['args']['channel_id']) + " owner: " + result['args'][
        'owner'] + " storage bytes: " + str(result['args']['storage_bytes']) + " lifetime: " + str(
        result['args']['lifetime']) + " number of nodes: " + str(result['args']['number_of_nodes']))


def basic_channel_added_callback(result):
    print("Basic channel added. aggregationChannelID: " + str(
        result['args']['aggregation_channel_id']) + " basicChannelID: " + str(result['args']['basic_channel_id']))


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
basic_channel_created = contract.on('BasicChannelCreated')
basic_channel_created.watch(basic_channel_created_callback)
aggregation_channel_created = contract.on('AggregationChannelCreated')
aggregation_channel_created.watch(aggregation_channel_created_callback)
basic_channel_added = contract.on('BasicChannelAdded')
basic_channel_added.watch(basic_channel_added_callback)


print(
    str(token.call().balanceOf(web3.eth.accounts[0])) + " " + str(token.call().balanceOf(data['registration_address'])))
token.transact({'from': web3.eth.accounts[0]}).approve(data['registration_address'], 100)
time.sleep(30)

contract.transact({'from': web3.eth.accounts[0]}).deposit("10.11.0.1", 3333, 4444)
time.sleep(30)
print(
    str(token.call().balanceOf(web3.eth.accounts[0])) + " " + str(token.call().balanceOf(data['registration_address'])))
print(str(contract.call().getNodeStatus(1)))
'''
contract.transact({'from': web3.eth.accounts[0]}).createBasicChannel(web3.eth.accounts[0], 100, 100, 4)
time.sleep(30)
contract.transact({'from': web3.eth.accounts[0]}).createAggregationChannel(web3.eth.accounts[0], 100, 100, 4)
time.sleep(30)

contract.transact({'from': web3.eth.accounts[0]}).addToAggregationChannel(2, 1)
time.sleep(30)

contract.transact({'from': web3.eth.accounts[0]}).initWithdrawDeposit(1)
time.sleep(30)
print(str(contract.call().getNodeStatus(1)))
contract.transact({'from': web3.eth.accounts[0]}).completeWithdrawDeposit(1)
time.sleep(30)
print(str(contract.call().getNodeStatus(1)))
print(
    str(token.call().balanceOf(web3.eth.accounts[0])) + " " + str(token.call().balanceOf(data['registration_address'])))
'''