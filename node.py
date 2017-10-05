from web3 import Web3, HTTPProvider
import json


def my_callback(log):
    print(log)
    print(log['args'])


with open('data.json') as data_file:
    data = json.load(data_file)
web3 = Web3(HTTPProvider('http://localhost:8545'))
web3.personal.unlockAccount(web3.eth.accounts[0], "123", 0);  # unsecure
tokenContract = web3.eth.contract(contract_name='GEXToken', address=data['GEXToken'], abi=data['GEXToken_abi'])
gexContract = web3.eth.contract(contract_name='GexContract', address=data['GexContract'], abi=data['GexContract_abi'])
ethContract = web3.eth.contract(contract_name='EthContract', address=data['EthContract'], abi=data['EthContract_abi'])

event = tokenContract.on('Mint')
event.watch(my_callback)

print tokenContract.call().balanceOf(web3.eth.accounts[0])
tokenContract.transact({'from': web3.eth.accounts[0]}).mint(web3.eth.accounts[0], 100)
while True:
    pass
