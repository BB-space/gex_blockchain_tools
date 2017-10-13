from web3 import Web3, HTTPProvider
import json
import time
import ecdsa
from ethereum import utils


def search_nodes_callback(result):
    print(result['args'])


with open('data.json') as data_file:
    data = json.load(data_file)

web3 = Web3(HTTPProvider('http://localhost:8545'))
testContract = web3.eth.contract(contract_name='Test', address=data['Test'],
                                 abi=data['Test_abi'])

ecContract = web3.eth.contract(contract_name='ECVerify', address=data['ECVerify'],
                               abi=data['ECVerify_abi'])

# web3.personal.unlockAccount(web3.eth.accounts[0], "123", 0)

# pr = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
# pub = pr.get_verifying_key()
message = "hello!"

# sig = pr.sign(message)
# print pub.to_string().encode("hex")
# print testContract.transact({'from': web3.eth.accounts[0]}).check(message, sig)
# search_nodes_event = testContract.on('Result')
# search_nodes_event.watch(search_nodes_callback)
# web3.sha3(message)

# search_nodes_event1 = ecContract.on('Result')
# search_nodes_event1.watch(search_nodes_callback)
# hash_op = web3.sha3(message)


hex_str = "0xAD4"
print hex(int(hex_str, 16))

print(web3.eth.accounts[0])
signature = web3.eth.sign(web3.eth.accounts[0], message)
print signature
r = "0x" + str(long(signature[0:66], 16))
s = "0x" + str(long('0x' + signature[66:130], 16))
v = long('0x' + signature[130:132], 16)
print r
print s
print v
if not (v == 27 and v == 28):
    v += 27
hash_msg = utils.sha3(message).encode('hex')
print testContract.call().constVerify(message, message, v, message)

# print testContract.call().verify_new(message, signature)



# while True:
#    pass
