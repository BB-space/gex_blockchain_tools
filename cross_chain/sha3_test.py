from web3 import Web3, HTTPProvider
import json
from sign import sha3

with open('data.json') as data_file:
    data = json.load(data_file)

web3 = Web3(HTTPProvider('http://localhost:8545'))
Test = web3.eth.contract(contract_name='Test', address=data['Test'],
                         abi=data['Test_abi'])
message = "secret"
web3.personal.unlockAccount(web3.eth.accounts[0], "123", 0)
print(web3.toHex(sha3(message)))
print(web3.toHex(Test.call({'from': web3.eth.accounts[0]}).compute_sha(message)))
print(web3.toHex(sha3(message, message)))
print(web3.toHex(Test.call({'from': web3.eth.accounts[0]}).sha_args(message, message)))
print(web3.toHex(sha3(22, web3.eth.accounts[0], 33)))
print(web3.toHex(Test.call({'from': web3.eth.accounts[0]}).sha(22, web3.eth.accounts[0], 33)))