from web3 import Web3, HTTPProvider
from flask import Flask, request
from common import TransferType
from graphene import ObjectType, String, Schema
from flask_graphql import GraphQLView
import json

'''
       class Query(ObjectType):
           hello = String(description='Hello')

           def resolve_hello(self, args, context, info):
               event_id = args.get('event_id')
               if event_id in Node.events:

               return 'World'
   '''


class Node:
    account_password = "123"
    password_unlock_duration = 120
    flask_port = 3333
    app = Flask(__name__)
    events = []

    @app.route('/sign', methods=['POST'])
    def sign(self):
        # todo here!!!!
        event_id = request.form['event_id']
        if event_id in self.events:
            print("Sign call from " + event_id)
            key = request.form['key']
            transfer_type = request.form['type']
            if self.validate_signature(key):
                self.web3eth.personal.unlockAccount(self.web3eth.eth.accounts[0], self.account_password,
                                                    self.password_unlock_duration)  # todo unsecure
                # todo get amount and new_key
                amount = 100
                new_key = "ll"
                self.gexContract.transact({'from': self.web3eth.eth.accounts[0]}).burnRequest(new_key, amount)
        else:
            print("Wrong sign request!")

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
        search_nodes_event = self.gexContract.on('SearchNodes')
        search_nodes_event.watch(self.search_nodes_callback)
        eth_token_burned_event = self.ethContract.on('TokenBurned')
        eth_token_burned_event.watch(self.eth_token_burned_callback)
        gex_token_burned_event = self.gexContract.on('TokenBurned')
        gex_token_burned_event.watch(self.gex_token_burned_callback)
        # init Flask server
        self.init_flask()

    def init_flask(self):
        # view_func = GraphQLView.as_view('graphql', schema=Schema(query=Query))
        # app.add_url_rule('/', view_func=view_func)
        self.app.run(host='0.0.0.0', port=self.flask_port)

    def validate_signature(self, key):
        # todo validate only once
        return True

    def is_validator(self, event_id):
        # todo
        return True

    def validate_contracts_identity(self, event_id):
        # todo
        return True

    def eth_token_burned_callback(self, result):
        self.burned_event_callback(result, False)

    def gex_token_burned_callback(self, result):
        self.burned_event_callback(result, True)

    def burned_event_callback(self, result, from_gex):
        print(result['args'])
        event_id = result['args']['event_id']
        if event_id in self.events:
            print("Burn callback for " + event_id)
            # todo check transaction
            if from_gex:
                self.web3eth.personal.unlockAccount(self.web3eth.eth.accounts[0], self.account_password,
                                                    self.password_unlock_duration)  # todo unsecure
                self.gexContract.transact({'from': self.web3eth.eth.accounts[0]}).mint(event_id)
            else:
                self.web3gex.personal.unlockAccount(self.web3gex.eth.accounts[0], self.account_password,
                                                    self.password_unlock_duration)  # todo unsecure
                self.gexContract.transact({'from': self.web3gex.eth.accounts[0]}).mint(event_id)

    def search_nodes_callback(self, result):
        print(result['args'])
        event_id = result['args']['event_id']
        if self.is_validator(event_id):
            self.web3gex.personal.unlockAccount(self.web3gex.eth.accounts[0], self.account_password,
                                                self.password_unlock_duration)  # todo unsecure
            if self.gexContract.transact({'from': self.web3gex.eth.accounts[0]}).register(event_id):
                print("Registered for event " + event_id)
                if self.validate_contracts_identity(event_id):
                    self.events.append(event_id)
                    print("Contracts identity is verified")
                else:
                    print("Contracts identity verification is failed")
            else:
                print("Registration for event " + event_id + " is failed")


node = Node()
while True:
    pass
