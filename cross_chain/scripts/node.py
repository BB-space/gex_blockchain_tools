from web3 import Web3, HTTPProvider
import json
try:
    from .config import *
except SystemError:
    from config import *


class Node:
    events = []

    def __init__(self):
        with open(FILE_PATH) as data_file:
            data = json.load(data_file)

        self.web3gex = Web3(HTTPProvider(gex_chain))
        self.web3eth = Web3(HTTPProvider(eth_chain))
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

    def burned_event_callback(self, result, is_gex_net):
        print("Token burned")
        event_id = self.web3gex.toHex(result['args']['event_id'])
        if event_id in self.events:
            print("Minting")
            if is_gex_net:
                self.web3eth.personal.unlockAccount(eth_node_transact_account, password, password_unlock_duration)  # todo unsecure
                self.ethContract.transact({'from': eth_node_transact_account}).mint(result['args']['event_id'])
            else:
                self.web3gex.personal.unlockAccount(gex_node_transact_account, password, password_unlock_duration)  # todo unsecure
                self.gexContract.transact({'from': gex_node_transact_account}).mint(result['args']['event_id'])

    def search_nodes_callback(self, result, is_gex_net):
        print("Search nodes")
        event_id = self.web3gex.toHex(result['args']['event_id'])
        if self.is_validator(event_id):
            print("Node is validator")
            if is_gex_net:
                self.web3gex.personal.unlockAccount(gex_node_transact_account, password, password_unlock_duration)  # todo unsecure
                self.gexContract.transact({'from': gex_node_transact_account}).register(result['args']['event_id'])
            else:
                self.web3eth.personal.unlockAccount(eth_node_transact_account, password, password_unlock_duration)  # todo unsecure
                self.ethContract.transact({'from': eth_node_transact_account}).register(result['args']['event_id'])
        # todo if the same in 2 nets
        # todo check that added
        self.events.append(event_id)

''''
node = Node()
print("Node started")
while True:
    pass
'''
