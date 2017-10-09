from web3 import Web3, HTTPProvider
import json
import uuid


class Transfer:
    public_destruction_key = None
    private_destruction_key = None
    address = None
    amount = 0

    def __init__(self):
        self.transfer_id = uuid.uuid4().hex


# todo single instance
class User:
    account_password = "123"
    password_unlock_duration = 120
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
        node_registration_finished_event = self.gexContrac.on('NodesRegistrationFinished')
        node_registration_finished_event.watch(self.node_registration_finished_callback)

    def create_transfer(self, address, amount):
        transfer = self.generate_destruction_keys()
        transfer.address = address
        transfer.amount = amount
        self.web3gex.personal.unlockAccount(self.web3gex.eth.accounts[0], self.account_password,
                                            self.password_unlock_duration)  # todo unsecure
        self.gexContract.transact({'from': self.web3gex.eth.accounts[0]}).mintRequest(transfer.amount)
        self.transfers[transfer.transfer_id] = transfer

    def generate_destruction_keys(self):
        # todo
        transfer = Transfer()
        transfer.public_destruction_key = "111"
        transfer.private_destruction_key = "222"
        return transfer

    def node_registration_finished_callback(self, result):
        # todo send id to contract
        # here and next event_id == transfer_id
        print(result['args'])
        transfer_id = result['args']['event_id']
        if transfer_id in self.transfers:
            transfer = self.transfers[transfer_id]
            # todo get public_keys and ip
            self.gexContract.call()


user = User()
while True:
    pass
