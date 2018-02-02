import json
import time

from populus_utils import *
from web3 import HTTPProvider


class TestHeartbit:
    def __init__(self):
        with open('../../data.json') as data_file:
            self.data = json.load(data_file)
        self.web3 = Web3(HTTPProvider("http://localhost:8545"))
        #self.web3 = Web3(HTTPProvider("http://51.0.1.99:8545"))
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
        mchain_created = self.contract.on('MchainCreated')
        mchain_created.watch(self.mchain_created_callback)
        aggregation_mchain_created = self.contract.on('AggregationMchainCreated')
        aggregation_mchain_created.watch(self.aggregation_mchain_created_callback)
        mchain_added = self.contract.on('MchainAdded')
        mchain_added.watch(self.mchain_added_callback)

        ''''''
        test1 = self.contract.on('Test1')
        test1.watch(self.test1)

        test2 = self.contract.on('Test2')
        test2.watch(self.test2)

        test3 = self.contract.on('NumberEvent')
        test3.watch(self.test3)


    def test2(self, result):
        print("test2")

    def test3(self, result):
        print("NumberEvent " + result['args']['num'])

    def test1(self, result):
        print("test1 ")

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

    def mchain_created_callback(self, result):
        print("Basic mchain created. mchainID: " + str(result['args']['mchainID']) + " owner: " + result['args'][
            'owner'] + " storage bytes: " + str(result['args']['storageBytes']) + " deposit: " + str(
            result['args']['deposit']) + " lifetime: " + str(
            result['args']['lifetime']) + " max nodes: " + str(result['args']['maxNodes']) + " nonce: " + str(
            result['args']['nonce']))

    def aggregation_mchain_created_callback(self, result):
        print(
            "Aggregation mchain created. mchainID: " + str(result['args']['mchainID']) + " owner: " + result['args'][
                'owner'] + " storage bytes: " + str(result['args']['storageBytes']) + " deposit: " + str(
                result['args']['deposit']) + " lifetime: " + str(
                result['args']['lifetime']) + " max nodes: " + str(result['args']['maxNodes']) + " nonce: " + str(
                result['args']['nonce']))

    def mchain_added_callback(self, result):
        print("Basic mchain added. aggregationMchainID: " + str(result['args']['aggregationMchainID']) +
              " MchainID: " + str(result['args']['MchainID']) + " nonce: " + str(result['args']['nonce']))

    def getGasUsed(self, tx, name):
        receipt = check_successful_tx(self.web3, tx)
        print(name + " " + str(receipt['gasUsed']))

    def test_deposit(self, ip, port, nonce):
        type = 0x1
        data = type.to_bytes(1, byteorder='big') + port.to_bytes(4, byteorder='big') + nonce.to_bytes(4,
                    byteorder='big') + ip.encode()
        #print(data)
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        self.getGasUsed(self.token.transact({'from': self.web3.eth.accounts[0]}).transfer(
            self.data['node_manager_address'], 100000000000000000000, data), "node create")

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

    def test_mchain_creation(self, storage_bytes, lifetime, max_nodes, nonce):
        type = 0x10
        data = type.to_bytes(1, byteorder='big') + storage_bytes.to_bytes(32, byteorder='big') + lifetime.to_bytes(32,
                    byteorder='big') + max_nodes.to_bytes(
            32, byteorder='big') + nonce.to_bytes(4, byteorder='big')
        # print(data)
        # print(self.contract.call().fallbackCreateMchainDataConvert(data))

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        self.getGasUsed(self.token.transact({
            'from': self.web3.eth.accounts[0]}).transfer(self.data['node_manager_address'], 100, data), "basic mchain")
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

    def test_aggregation_mchain_creation(self, storage_bytes, lifetime, max_nodes, nonce):
        type = 0x11
        data = type.to_bytes(1, byteorder='big') + storage_bytes.to_bytes(32, byteorder='big') + lifetime.to_bytes(32,
                            byteorder='big') + max_nodes.to_bytes(
            32, byteorder='big') + nonce.to_bytes(4, byteorder='big')
        # print(data)
        # print(self.contract.call().fallbackCreateMchainDataConvert(data))

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        self.getGasUsed(self.token.transact({
            'from': self.web3.eth.accounts[0]}).transfer(self.data['node_manager_address'], 100, data),
             "aggregation mchain")
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

    def test_withdraw_mchains(self):
         #self.test_mchain_creation(98764, 1, 12345, 4444)
         print(test.contract.call().getMchains())
         self.getGasUsed(self.contract.transact({
            'from': self.web3.eth.accounts[0]}).withdrawFromMchains(),"withdraw from mchain")
         print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
             self.token.call().balanceOf(self.data['node_manager_address'])))
         print(test.contract.call().getMchains())

    def test_withdraw_mchain(self):
        #self.test_mchain_creation(98764, 1, 12345, 4444)
        #self.test_mchain_creation(98764, 1, 12345, 4444)
        print(test.contract.call().getMchainList())
        print(test.contract.call().getMchain(0))
        print(test.contract.call().getMchain(1))
        self.getGasUsed(self.contract.transact({
            'from': self.web3.eth.accounts[0]}).withdrawFromMchain(0), "withdraw from mchain")
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        print(test.contract.call().getMchainList())

    def test_add_mchain(self, aggregation_index, basic_index, nonce):
         self.getGasUsed(self.contract.transact({
            'from': self.web3.eth.accounts[0]}).addToAggregationMchain(aggregation_index, basic_index, nonce ),
             "add basic mchain")


test = TestHeartbit()

print(test.contract.call().getMchain(0))
print(test.contract.call().getMchain(1))

test.test_withdraw_mchain()
print(test.contract.call().getMchain(0))
print(test.contract.call().getMchain(1))
#print(test.contract.call().getNodeIPs())

#print(test.contract.call().getNode(2))

#test.test_deposit("255.255.255.255", 6000, 12345)
#test.contract.transact({'from': test.web3.eth.accounts[0]}).setNumber(6)
#print(test.contract.call().getNumber())

#test.test_deposit("10.255.255.255", 6000, 12345)
#test.test_deposit("255.255.255.255", 6000, 12345)
#time.sleep(30)
'''
test.test_mchain_creation(98764, 6000, 12345, 4444) 

 
id = test.contract.call().getActiveNodeIDs()
print(test.contract.call().getActiveNodeIPs(id))

print(test.contract.call().getNodeIPs())


test.test_mchain_creation(98764, 6000, 12345, 4444)
test.test_mchain_creation(11111, 55, 2, 5555)
test.test_mchain_creation(222, 155, 24, 53555)

test.test_aggregation_mchain_creation(98764, 6000, 12345, 4444)
test.test_aggregation_mchain_creation(11111, 55, 2, 5555)
test.test_aggregation_mchain_creation(222, 155, 24, 53555)


#test.test_mchain_creation(98764, 6000, 12345, 4444)

test.test_mchain_creation(98764, 1, 12345, 4444)
test.test_mchain_creation(98643, 10000, 12345, 4443)
test.test_mchain_creation(98764, 1, 12345, 4444)
test.test_mchain_creation(98643, 1000, 12345, 4443)
test.test_aggregation_mchain_creation(222, 6000, 24, 53555)
test.test_add_mchain(1, 1, 53555)
print(test.contract.call().getMchainListFromAggregationMchain(1))
print(test.contract.call().getMchains())
time.sleep(5)
test.test_withdraw_mchain()
print(test.contract.call().getMchains())
'''