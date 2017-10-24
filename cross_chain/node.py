from web3 import Web3, HTTPProvider
import json
import sys
import time


class Node:
    password = "123"
    password_unlock_duration = 120
    events = []

    def __init__(self, timeout=0):
        self.timeout = int(timeout)
        with open('./../data.json') as data_file:
            data = json.load(data_file)

        self.web3gex = Web3(HTTPProvider('http://localhost:8545'))
        self.web3eth = Web3(HTTPProvider('http://localhost:8545'))
        self.gexContract = self.web3gex.eth.contract(contract_name='GexContract', address=data['GexContract'],
                                                     abi=data['GexContract_abi'])
        self.ethContract = self.web3eth.eth.contract(contract_name='EthContract', address=data['EthContract'],
                                                     abi=data['EthContract_abi'])
        # event listeners
        gex_search_nodes_event = self.gexContract.on('SearchNodes')
        gex_search_nodes_event.watch(self.gex_search_nodes_callback)
        gex_token_burned_event = self.gexContract.on('TokenBurned')
        gex_token_burned_event.watch(self.gex_token_burned_callback)
        gex_token_minted_event = self.gexContract.on('TokenMinted')
        gex_token_minted_event.watch(self.minted_event_callback)
        eth_search_nodes_event = self.ethContract.on('SearchNodes')
        eth_search_nodes_event.watch(self.eth_search_nodes_callback)
        eth_token_burned_event = self.ethContract.on('TokenBurned')
        eth_token_burned_event.watch(self.eth_token_burned_callback)
        eth_token_minted_event = self.ethContract.on('TokenMinted')
        eth_token_minted_event.watch(self.minted_event_callback)

        gex_test3_event = self.gexContract.on('Test3')
        eth_test3_event = self.ethContract.on('Test3')
        gex_test3_event.watch(self.callback3)
        eth_test3_event.watch(self.callback3)
        gex_test4_event = self.gexContract.on('Test4')
        eth_test4_event = self.ethContract.on('Test4')
        gex_test4_event.watch(self.callback4)
        eth_test4_event.watch(self.callback4)
        gex_test5_event = self.gexContract.on('Test5')
        eth_test5_event = self.ethContract.on('Test5')
        gex_test5_event.watch(self.callback5)
        eth_test5_event.watch(self.callback5)
        gex_test6_event = self.gexContract.on('Test6')
        eth_test6_event = self.ethContract.on('Test6')
        gex_test6_event.watch(self.callback6)
        eth_test6_event.watch(self.callback6)

    def is_validator(self, event_id):
        # todo
        return True

    def eth_token_burned_callback(self, result):
        self.burned_event_callback(result, False)

    def gex_token_burned_callback(self, result):
        self.burned_event_callback(result, True)

    def eth_search_nodes_callback(self, result):
        self.search_nodes_callback(result, False)

    def gex_search_nodes_callback(self, result):
        self.search_nodes_callback(result, True)

    def minted_event_callback(self, result):
        print("Token minted")

    def callback3(self, result):
        print("Test3")

    def callback4(self, result):
        print("Test4")
        print(result)

    def callback5(self, result):
        print("Test5")

    def callback6(self, result):
        print("Test6")

    def burned_event_callback(self, result, is_gex_net):
        print("Token burned")
        event_id = self.web3gex.toHex(result['args']['event_id'])
        if event_id in self.events:
            print("Minting")
            time.sleep(self.timeout)
            if is_gex_net:
                self.web3eth.personal.unlockAccount(self.web3eth.eth.accounts[0], self.password,
                                                    self.password_unlock_duration)  # todo unsecure
                self.ethContract.transact({'from': self.web3eth.eth.accounts[0]}).mint(result['args']['event_id'])
            else:
                self.web3gex.personal.unlockAccount(self.web3gex.eth.accounts[0], self.password,
                                                    self.password_unlock_duration)  # todo unsecure
                self.gexContract.transact({'from': self.web3gex.eth.accounts[0]}).mint(result['args']['event_id'])

    def search_nodes_callback(self, result, is_gex_net):
        print("Search nodes")
        event_id = self.web3gex.toHex(result['args']['event_id'])
        if self.is_validator(event_id):
            print("Node is validator")
            if is_gex_net:
                self.web3gex.personal.unlockAccount(self.web3gex.eth.accounts[0], self.password,
                                                    self.password_unlock_duration)  # todo unsecure
                self.gexContract.transact({'from': self.web3gex.eth.accounts[0]}).register(result['args']['event_id'])
            else:
                self.web3eth.personal.unlockAccount(self.web3eth.eth.accounts[0], self.password,
                                                    self.password_unlock_duration)  # todo unsecure
                self.ethContract.transact({'from': self.web3eth.eth.accounts[0]}).register(result['args']['event_id'])
        # todo if the same in 2 nets
        # todo check that added
        self.events.append(event_id)


node = Node(sys.argv[1])
print("Node started")
while True:
    pass
