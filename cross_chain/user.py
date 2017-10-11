from web3 import Web3, HTTPProvider
from collections import namedtuple
from common import TransferType
import json
import uuid

Node = namedtuple('Node', 'address ip key')


class Transfer:
    public_destruction_key = None
    private_destruction_key = None
    address = None
    amount = 0
    nodes = []
    type = None

    def __init__(self):
        self.event_id = uuid.uuid4().hex


# todo check that mint is finished
# todo single instance
class User:
    account_password = "123"  # same pass for both networks
    password_unlock_duration = 120
    transfers = {}

    def __init__(self):
        with open('data.json') as data_file:
            data = json.load(data_file)

        self.web3gex = Web3(HTTPProvider('http://localhost:8545'))
        self.web3eth = Web3(HTTPProvider('http://localhost:8545'))
        self.gexContract = self.web3gex.eth.contract(contract_name='GexContract', address=data['GexContract'],
                                                     abi=data['GexContract_abi'])
        self.nodeContract = self.web3gex.eth.contract(contract_name='NodeContract', address=data['NodeContract'],
                                                      abi=data['NodeContract_abi'])
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
        transfer = self.generate_destruction_keys()
        transfer.address = address
        transfer.amount = amount
        transfer.type = TransferType[transfer_type]
        # todo unsecure
        self.web3gex.personal.unlockAccount(self.web3gex.eth.accounts[0], self.account_password,
                                            self.password_unlock_duration)
        self.web3gex.personal.unlockAccount(self.web3eth.eth.accounts[0], self.account_password,
                                            self.password_unlock_duration)
        if type == TransferType.gex_to_eth.name:
            # todo change accounts
            self.gexContract.transact({'from': self.web3gex.eth.accounts[0]}).burnRequest(transfer.event_id,
                                                                                          transfer.public_destruction_key,
                                                                                          transfer.amount)
            self.gexContract.transact({'from': self.web3eth.eth.accounts[0]}).mintRequest(transfer.event_id,
                                                                                          transfer.amount)
        else:
            self.gexContract.transact({'from': self.web3gex.eth.accounts[0]}).mintRequest(transfer.event_id,
                                                                                          transfer.amount)
            self.gexContract.transact({'from': self.web3eth.eth.accounts[0]}).burnRequest(transfer.event_id,
                                                                                          transfer.public_destruction_key,
                                                                                          transfer.amount)
        self.transfers[transfer.event_id] = transfer

    def generate_destruction_keys(self):
        transfer = Transfer()
        # todo generate keys
        transfer.public_destruction_key = "111"
        transfer.private_destruction_key = "222"
        return transfer

    def node_registration_finished_callback(self, result):
        print(result['args'])
        event_id = result['args']['event_id']
        if event_id in self.transfers:
            transfer = self.transfers[event_id]
            validators = self.gexContract.call().getValidators(event_id)
            for validator in validators:
                node = Node(validator, self.nodeContract.call().getIp(validator),
                            self.nodeContract.call().getPublicKey(validator))
                transfer.nodes.append(node)
            self.send_key_to_nodes(transfer)
        else:
            print("Invalid event")

    def send_key_to_nodes(self, transfer):
        for node in transfer.nodes:
            # todo
            pass


user = User()
while True:
    pass
