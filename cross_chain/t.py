from _pysha3 import sha3_256

from web3 import Web3, HTTPProvider
import json
from eth_utils import decode_hex
import sha3

def callback(result):
    print(web3.toHex(result['args']['event_id']))


with open('data.json') as data_file:
    data = json.load(data_file)

web3 = Web3(HTTPProvider('http://localhost:8545'))
Test = web3.eth.contract(contract_name='Test', address=data['Test'],
                         abi=data['Test_abi'])
verify = Test.on('GetSha')
verify.watch(callback)

message = "secret"
print web3.sha3(text=message, encoding='None')
print web3.soliditySha3(['bytes'], ['0x'+message.encode('hex')])
#sha3_256(message).hexdigest()
#sha_python =  web3.sha3(text=message, encoding='None')

web3.personal.unlockAccount(web3.eth.accounts[0], "123", 0)
print web3.toHex(Test.call({'from': web3.eth.accounts[0]}).compute_sha(message))
print web3.toHex(Test.call({'from': web3.eth.accounts[0]}).sha_args(message, "10"))

def callback(result):
    print("Argument: " + result['args']['event_id'].encode("hex"))


#while True:
#    pass
