import json
from web3 import HTTPProvider, Web3
import time

class TestHeartbit:

    def __init__(self):
        with open('../../data1.json') as data_file:
            self.data = json.load(data_file)
        self.web3 = Web3(HTTPProvider("http://localhost:8545"))
        #self.web3 = Web3(HTTPProvider("http://51.0.1.99:8545"))
        self.contract = self.web3.eth.contract(contract_name='NodeManager', address=self.data['node_manager_address'],
                                     abi=self.data['node_manager_abi'])
        self.token = self.web3.eth.contract(contract_name='Token', address=self.data['token_address'], abi=self.data['token_abi'])
        approval = self.token.on('Approval')
        approval.watch(self.approval_callback)
        transfer = self.token.on('Transfer')
        transfer.watch(self.transfer_callback)
        node_created = self.contract.on('NodeCreated')
        node_created.watch(self.node_created_callback)
        basic_channel_created = self.contract.on('BasicChannelCreated')
        basic_channel_created.watch(self.basic_channel_created_callback)
        basic = self.contract.on('Basic')
        basic.watch(self.basic_callback)
        aggregation = self.contract.on('Aggregation')
        aggregation.watch(self.aggregation_callback)
        aggregation_channel_created = self.contract.on('AggregationChannelCreated')
        aggregation_channel_created.watch(self.aggregation_channel_created_callback)
        basic_channel_added = self.contract.on('BasicChannelAdded')
        basic_channel_added.watch(self.basic_channel_added_callback)

    def approval_callback(self, result):
        print("Approval. owner: " + result['args']['_owner'] + " spender: " + result['args'][
            '_spender'] + " value: " + str(result['args']['_value']))

    def transfer_callback(self, result):
        print("Transfer. from: " + result['args']['_from'] + " to: " + result['args']['_to'] + " value: " + str(result['args']['_value'])
              + " data: " + str(result['args']['_data']))

    def node_created_callback(self, result):
        print("Node Created. nodeID: " + str(result['args']['nodeID']) + " nodeIP: " + result['args'][
            'ip'] + " port: " + str(result['args']['port']) + " nonce: " + str(result['args']['nonce']))

    def basic_callback(self, result):
        print("Basic")

    def aggregation_callback(self, result):
        print("Aggregation")

    def basic_channel_created_callback(self, result):
        print("Basic channel created. channelID: " + str(result['args']['channelID']) + " owner: " + result['args'][
            'owner'] + " storage bytes: " + str(result['args']['storageBytes']) + " deposit: " + str(result['args']['deposit']) + " lifetime: " + str(
            result['args']['lifetime']) + " max nodes: " + str(result['args']['maxNodes']) + " nonce: " + str(result['args']['nonce']))

    def aggregation_channel_created_callback(self, result):
        print("Aggregation channel created. channelID: "  + str(result['args']['channelID']) + " owner: " + result['args'][
            'owner'] + " storage bytes: " + str(result['args']['storageBytes'])  + " deposit: " + str(result['args']['deposit']) + " lifetime: " + str(
            result['args']['lifetime']) + " max nodes: " + str(result['args']['maxNodes']) + " nonce: " + str(result['args']['nonce']))

    def basic_channel_added_callback(self, result):
        print("Basic channel added. aggregationChannelID: " + str(result['args']['aggregationChannelID']) +
              " basicChannelID: " + str(result['args']['basicChannelID']) + " nonce: " + str(result['args']['nonce']))

    def test_deposit(self):
        type = 0x1
        ip = "255.255.255.255"
        port = 6000
        nonce = 12345
        data = type.to_bytes(1, byteorder='big') + port.to_bytes(4, byteorder='big') + nonce.to_bytes(4, byteorder='big') + ip.encode()
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
                self.token.call().balanceOf(self.data['node_manager_address'])))
        self.token.transact({'from': self.web3.eth.accounts[0]}).transfer(self.data['node_manager_address'], 100000000000000000000, data)
        time.sleep(40)
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
                self.token.call().balanceOf(self.data['node_manager_address'])))

    def test_basic_channel_creation(self):
        type = 0x10
        storage_bytes = 98765
        lifetime = 6000
        max_nodes = 12345
        nonce = 4444
        data = type.to_bytes(1, byteorder='big') + storage_bytes.to_bytes(32, byteorder='big') + lifetime.to_bytes(32,
                             byteorder='big') + max_nodes.to_bytes(32, byteorder='big') + nonce.to_bytes(4, byteorder='big')
        print(data)
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        self.token.transact({'from': self.web3.eth.accounts[0]}).transfer(self.data['node_manager_address'],100, data)
        time.sleep(40)
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))


test = TestHeartbit()
#test.test_deposit()
test.test_basic_channel_creation()

