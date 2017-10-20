from web3 import Web3, HTTPProvider
from enum import Enum
import json
from sign import sha3

# 'gex_to_eth' means that token is transferring from GEX notwork to Ethereum network.
# The same way 'eth_to_gex' corresponds to transfer from Ethereum to GEX.
TransferType = Enum('TransferType', 'gex_to_eth eth_to_gex')


class Transfer:
    def __init__(self, address, amount, transfer_type, web3_gex, web3_eth, gex_contract, eth_contract):
        self.address = address
        self.amount = amount
        self.transfer_type = transfer_type
        if type == TransferType.gex_to_eth.name:
            self.burning_net = web3_gex
            self.minting_net = web3_eth
            self.burning_contract = gex_contract
            self.minting_contract = eth_contract
        else:
            self.burning_net = web3_eth
            self.minting_net = web3_gex
            self.burning_contract = eth_contract
            self.minting_contract = gex_contract
        self.block_number = self.minting_net.eth.blockNumber
        self.event_id = web3_gex.toHex(sha3(self.block_number, address, amount))


# todo check that mint is finished
# todo single instance
class User:
    # todo save passwords
    password = "123"
    password_unlock_duration = 120
    flask_port = 3333
    transfers = {}

    def __init__(self):
        with open('data.json') as data_file:
            data = json.load(data_file)

        self.web3gex = Web3(HTTPProvider('http://localhost:8545'))
        self.web3eth = Web3(HTTPProvider('http://localhost:8545'))
        self.gexContract = self.web3gex.eth.contract(contract_name='GexContract', address=data['GexContract'],
                                                     abi=data['GexContract_abi'])
        self.ethContract = self.web3eth.eth.contract(contract_name='EthContract', address=data['EthContract'],
                                                     abi=data['EthContract_abi'])

        # event listeners
        node_registration_finished_event = self.gexContract.on('NodesRegistrationFinished')
        node_registration_finished_event.watch(self.node_registration_finished_callback)

    def create_transfer(self, transfer_type, address, amount):
        if transfer_type not in TransferType.__members__:
            print("Invalid transfer type")
            # todo remove exit
            exit(1)
        if amount <= 0:
            print("Amount must be >0")
            # todo remove exit
            exit(1)
        # todo check address
        transfer = Transfer(address, amount, TransferType[transfer_type], self.web3gex, self.web3eth, self.gexContract,
                            self.ethContract)
        transfer.minting_net.personal.unlockAccount(transfer.address, self.password, self.password_unlock_duration)
        transfer.minting_contract.transact({'from': transfer.address}).mintRequest(transfer.block_number,
                                                                                   transfer.address, transfer.amount)
        self.transfers[transfer.event_id] = transfer

    def node_registration_finished_callback(self, result):
        print(result['args'])
        event_id = result['args']['event_id']
        if event_id in self.transfers:
            transfer = self.transfers[event_id]
            transfer.burning_at.personal.unlockAccount(transfer.address, self.password, self.password_unlock_duration)
            transfer.burning_contract.transact({'from': transfer.address}).burn(transfer.event_id,
                                                                                transfer.block_number,
                                                                                transfer.address,
                                                                                transfer.amount)


user = User()
while True:
    pass
