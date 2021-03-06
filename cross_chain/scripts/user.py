from web3 import Web3, HTTPProvider
import json
import time
import sys

sys.path.append('../../gex_chain')
from sign import sha3

try:
    from .config import *
except SystemError:
    from config import *


# 'is_gex_net' means that token is transferring (burning) from GEX network to Ethereum network (minting).
class Transfer:
    def __init__(self, addr_from, addr_to, amount, is_gex_net, web3_gex, web3_eth, gex_contract, eth_contract):
        self.addr_from = addr_from
        self.addr_to = addr_to
        self.amount = amount
        self.is_gex_net = is_gex_net
        if is_gex_net:
            self.burning_net = web3_gex
            self.minting_net = web3_eth
            self.burning_contract = gex_contract
            self.minting_contract = eth_contract
            print("burning in gex, minting in eth")
        else:
            self.burning_net = web3_eth
            self.minting_net = web3_gex
            self.burning_contract = eth_contract
            self.minting_contract = gex_contract
            print("burning in eth, minting in gex")
        self.block_number = self.minting_net.eth.blockNumber
        self.event_id = web3_gex.toHex(sha3(self.block_number, addr_from, addr_to, amount))


# todo save events to db
# todo save passwords
class User:
    transfers = {}

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
        gex_node_registration_finished_event = self.gexContract.on('NodesRegistrationFinished')
        gex_node_registration_finished_event.watch(self.node_registration_finished_callback)
        eth_node_registration_finished_event = self.ethContract.on('NodesRegistrationFinished')
        eth_node_registration_finished_event.watch(self.node_registration_finished_callback)

        gex_gas_event = self.gexContract.on('GasCost')
        gex_gas_event.watch(self.gas_callback)
        eth_gas_event = self.ethContract.on('GasCost')
        eth_gas_event.watch(self.gas_callback)

    def create_transfer(self, is_gex_net, addr_from, addr_to, amount):
        # todo check other fields
        if amount <= 0:
            raise ValueError("Amount must be > 0")
        transfer = Transfer(addr_from, addr_to, amount, is_gex_net, self.web3gex, self.web3eth, self.gexContract,
                            self.ethContract)
        # todo change address
        transfer.minting_net.personal.unlockAccount(transfer.addr_to, password, password_unlock_duration)
        transfer.minting_contract.transact({'from': transfer.addr_to}).mintRequest(
            transfer.block_number, transfer.addr_from, transfer.addr_to, transfer.amount)
        self.transfers[transfer.event_id] = transfer

    def node_registration_finished_callback(self, result):
        print("Node registration finished")
        event_id = self.web3gex.toHex(result['args']['event_id'])
        if event_id in self.transfers:
            print("Burning")
            transfer = self.transfers[event_id]
            transfer.burning_net.personal.unlockAccount(transfer.addr_from, password, password_unlock_duration)
            transfer.burning_contract.transact({'from': transfer.addr_from}).burn(result['args']['event_id'],
                                                                                  transfer.block_number,
                                                                                  transfer.addr_from, transfer.addr_to,
                                                                                  transfer.amount)

    def gas_callback(self, result):
        pass
        # print(result['args']['_function_name'] + "  " + str(result['args']['_gaslimit']) + "  " + str(
        #    result['args']['_gas_remaining']))


def mint_callback(result):
    print("Mint")


def burn_callback(result):
    print("Burn")


''''
web3 = Web3(HTTPProvider('http://localhost:8545'))

with open('../data.json') as data_file:
    data = json.load(data_file)

gex_token = web3.eth.contract(contract_name='GEXToken', address=data['GEXToken'], abi=data['GEXToken_abi'])
eth_token = web3.eth.contract(contract_name='ETHToken', address=data['ETHToken'], abi=data['ETHToken_abi'])

gex_mint_event = gex_token.on('Mint')
gex_mint_event.watch(mint_callback)
gex_burn_event = gex_token.on('Burn')
gex_burn_event.watch(burn_callback)

eth_mint_event = eth_token.on('Mint')
eth_mint_event.watch(mint_callback)
eth_burn_event = eth_token.on('Burn')
eth_burn_event.watch(burn_callback)

user = User()
user.create_transfer(False, web3.eth.accounts[0], web3.eth.accounts[1], 10)
while True:
    print(str(gex_token.call().balanceOf(web3.eth.accounts[0])) + "   " + str(
        gex_token.call().balanceOf(web3.eth.accounts[1])) + "   "
          + str(eth_token.call().balanceOf(web3.eth.accounts[0])) + "   " + str(
        eth_token.call().balanceOf(web3.eth.accounts[1])))
    time.sleep(30)
'''
