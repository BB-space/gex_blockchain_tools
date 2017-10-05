from web3 import Web3, HTTPProvider
import json


class Node:
    account_password = "123"
    password_unlock_duration = 120

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
        search_nodes_event = self.gexContrac.on('SearchNodes')
        search_nodes_event.watch(self.search_nodes_callback)

    def is_validator(self, event_id):
        # todo
        return True

    def validate_contracts_identity(self, event_id):
        # todo
        return True

    def search_nodes_callback(self, log):
        print(log['args'])
        event_id = log['args']['id']
        if self.is_validator(event_id):
            # todo get pubKey and ip
            public_key = "lala"
            ip = "10.1.0.11"
            self.web3gex.personal.unlockAccount(self.web3gex.eth.accounts[0], self.account_password,
                                                self.password_unlock_duration)  # todo unsecure
            if self.gexContract.transact({'from': self.web3gex.eth.accounts[0]}).register(event_id, public_key, ip):
                print "Registered for event", event_id
                if self.validate_contracts_identity(event_id):
                    print "Contracts identity is verified"
                else:
                    print "Contracts identity verification is failed"
            else:
                print "Registration for event", event_id, "is failed"

                # .mint(self.web3gex.eth.accounts[0], 100)
                # tokenContract = web3.eth.contract(contract_name='GEXToken', address=data['GEXToken'], abi=data['GEXToken_abi'])
                # print tokenContract.call().balanceOf(web3.eth.accounts[0])
                # tokenContract.transact({'from': web3.eth.accounts[0]}).mint(web3.eth.accounts[0], 100)
                # while True:
                #    pass
