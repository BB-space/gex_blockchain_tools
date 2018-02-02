import json
from populus_utils import *
from web3 import HTTPProvider

class Basic:

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
