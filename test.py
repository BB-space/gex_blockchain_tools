from web3 import Web3, HTTPProvider
import json

def my_callback(log):
    print(log)
    print
    print(log['args'])
    pass

with open('data.json') as data_file:    
    data = json.load(data_file)
web3 = Web3(HTTPProvider('http://localhost:8545'))
#unsecure
web3.personal.unlockAccount(web3.eth.accounts[0], "123", 0);
#abi=json.loads(abi)
contract = web3.eth.contract(contract_name = 'GEXToken', address = data['GEXToken'], abi = data['GEXToken_abi'])

funded_filter = contract.on('Mint')
funded_filter.watch(my_callback)

print contract.call().balanceOf(web3.eth.accounts[0])
contract.transact({'from': web3.eth.accounts[0]}).mint(web3.eth.accounts[0],100)
while True:
    pass