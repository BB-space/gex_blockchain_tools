import json
import time

from populus_utils import *
from web3 import HTTPProvider


class TestHeartbit:
    def __init__(self):
        with open('../../data.json') as data_file:
            self.data = json.load(data_file)
        self.web3 = Web3(HTTPProvider("http://localhost:8545"))
        # self.web3 = Web3(HTTPProvider("http://51.0.1.99:8545"))
        self.contract = self.web3.eth.contract(contract_name='NodeManager', address=self.data['node_manager_address'],
                                               abi=self.data['node_manager_abi'])
        self.token = self.web3.eth.contract(contract_name='Token', address=self.data['token_address'],
                                            abi=self.data['token_abi'])
        approval = self.token.on('Approval')
        approval.watch(self.approval_callback)
        transfer = self.token.on('Transfer')
        transfer.watch(self.transfer_callback)
        node_created = self.contract.on('NodeCreated')
        node_created.watch(self.node_created_callback)
        basic_channel_created = self.contract.on('BasicChannelCreated')
        basic_channel_created.watch(self.basic_channel_created_callback)
        aggregation_channel_created = self.contract.on('AggregationChannelCreated')
        aggregation_channel_created.watch(self.aggregation_channel_created_callback)
        basic_channel_added = self.contract.on('BasicChannelAdded')
        basic_channel_added.watch(self.basic_channel_added_callback)

        test1 = self.contract.on('NumberEvent')
        test1.watch(self.test1)
        '''
        test2 = self.contract.on('Test2')
        test2.watch(self.test2)

    def test2(self, result):
        print("test2")
        '''

    def test1(self, result):
        print("test1 " + str(result['args']['num']))

    def gas_callback(self, result):
        print(result['args']['_function_name'] + " " + str(result['args']['_gaslimit']) + " " + str(
            result['args']['_gas_remaining']))

    def approval_callback(self, result):
        print("Approval. owner: " + result['args']['_owner'] + " spender: " + result['args'][
            '_spender'] + " value: " + str(result['args']['_value']))

    def transfer_callback(self, result):
        print("Transfer. from: " + result['args']['_from'] + " to: " + result['args']['_to'] + " value: " + str(
            result['args']['_value'])
              + " data: " + str(result['args']['_data']))

    def node_created_callback(self, result):
        print("Node Created. nodeID: " + str(result['args']['nodeID']) + " nodeIP: " + result['args'][
            'ip'] + " port: " + str(result['args']['port']) + " nonce: " + str(result['args']['nonce']))

    def basic_channel_created_callback(self, result):
        print("Basic channel created. channelID: " + str(result['args']['channelID']) + " owner: " + result['args'][
            'owner'] + " storage bytes: " + str(result['args']['storageBytes']) + " deposit: " + str(
            result['args']['deposit']) + " lifetime: " + str(
            result['args']['lifetime']) + " max nodes: " + str(result['args']['maxNodes']) + " nonce: " + str(
            result['args']['nonce']))

    def aggregation_channel_created_callback(self, result):
        print(
            "Aggregation channel created. channelID: " + str(result['args']['channelID']) + " owner: " + result['args'][
                'owner'] + " storage bytes: " + str(result['args']['storageBytes']) + " deposit: " + str(
                result['args']['deposit']) + " lifetime: " + str(
                result['args']['lifetime']) + " max nodes: " + str(result['args']['maxNodes']) + " nonce: " + str(
                result['args']['nonce']))

    def basic_channel_added_callback(self, result):
        print("Basic channel added. aggregationChannelID: " + str(result['args']['aggregationChannelID']) +
              " basicChannelID: " + str(result['args']['basicChannelID']) + " nonce: " + str(result['args']['nonce']))

    def test_deposit(self, ip, port, nonce):
        type = 0x1
        data = type.to_bytes(1, byteorder='big') + port.to_bytes(4, byteorder='big') + nonce.to_bytes(4,
                    byteorder='big') + ip.encode()
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        self.getGasUsed(self.token.transact({'from': self.web3.eth.accounts[0]}).transfer(
            self.data['node_manager_address'], 100000000000000000000, data), "node create")

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

    def test_basic_channel_creation(self, storage_bytes, lifetime, max_nodes, nonce):
        type = 0x10
        data = type.to_bytes(1, byteorder='big') + storage_bytes.to_bytes(32, byteorder='big') + lifetime.to_bytes(32,
                    byteorder='big') + max_nodes.to_bytes(
            32, byteorder='big') + nonce.to_bytes(4, byteorder='big')
        # print(data)
        # print(self.contract.call().fallbackCreateChannelDataConvert(data))

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        self.token.transact({'from': self.web3.eth.accounts[0]}).transfer(self.data['node_manager_address'], 100, data)
        time.sleep(20)
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

    def test_aggregation_channel_creation(self, storage_bytes, lifetime, max_nodes, nonce):
        type = 0x11
        data = type.to_bytes(1, byteorder='big') + storage_bytes.to_bytes(32, byteorder='big') + lifetime.to_bytes(32,
                            byteorder='big') + max_nodes.to_bytes(
            32, byteorder='big') + nonce.to_bytes(4, byteorder='big')
        # print(data)
        # print(self.contract.call().fallbackCreateChannelDataConvert(data))

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        self.token.transact({'from': self.web3.eth.accounts[0]}).transfer(self.data['node_manager_address'], 100, data)
        time.sleep(20)
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))


test = TestHeartbit()
# test.contract.transact({'from': test.web3.eth.accounts[0]}).setNumber(100)
# time.sleep(10)

test.test_deposit("255.255.255.255", 6000, 12345)
'''
test.test_deposit("10.255.255.255", 6000, 12345)
print(test.contract.call().getNodeIPs())

test.test_basic_channel_creation(98764, 6000, 12345, 4444)
test.test_basic_channel_creation(11111, 55, 2, 5555)
test.test_basic_channel_creation(222, 155, 24, 53555)
print(test.contract.call().getBasicChannels())
test.test_aggregation_channel_creation(98764, 6000, 12345, 4444)
test.test_aggregation_channel_creation(11111, 55, 2, 5555)
test.test_aggregation_channel_creation(222, 155, 24, 53555)
print(test.contract.call().getAggregationChannels())
'''
