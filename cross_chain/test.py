from web3 import Web3, HTTPProvider
import json
import time
import ecdsa

with open('data.json') as data_file:
    data = json.load(data_file)

web3 = Web3(HTTPProvider('http://localhost:8545'))
testContract = web3.eth.contract(contract_name='Test', address=data['Test'],
                                 abi=data['Test_abi'])
web3.personal.unlockAccount(web3.eth.accounts[0], "123", 0)

pr = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
pub = pr.get_verifying_key()
message = "\x19Ethereum Signed Message:\n1H"  #
sig = pr.sign(message)
#print pub.to_string().encode("hex")
# print testContract.transact({'from': web3.eth.accounts[0]}).check(message, sig)

# hash_op = web3.sha3(message)
print(web3.eth.accounts[0])
signature = web3.eth.sign(web3.eth.accounts[0], message)
print testContract.transact({'from': web3.eth.accounts[0]}).verify(message, signature)
0x83dafc7b3a6aeb5cf5db99cd7c334e887c02a9ff
0xcef813a7123f5bbef9a2f8c0affd9f44a26b50da74e3f43cf0f94e30035d90c8
