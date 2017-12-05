from web3 import HTTPProvider, Web3
import json
import time

def callbackk(result):
    print("Name: " + str(result['args']['name']))


with open('../data.json') as data_file:
    data = json.load(data_file)
web3 = Web3(HTTPProvider('http://localhost:8545'))
test = web3.eth.contract(contract_name='Test', address=data['registration_address'], abi=data['registration_abi'])
event = test.on('NewNumber')
event.watch(callbackk)
web3.personal.unlockAccount(web3.eth.accounts[0], '123', 0)
test.transact({'from': web3.eth.accounts[0]}).setNumber(9)
time.sleep(10)
print(test.call().getNumber())