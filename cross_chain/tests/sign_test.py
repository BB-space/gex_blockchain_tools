import binascii
from web3 import Web3, HTTPProvider
import json
import ecdsa
from web3.utils.encoding import encode_hex


# from web3.utils.formatting import remove_0x_prefix
def verify_callback(result):
    print("Argument: " + str(result['args']))


with open('./../data.json') as data_file:
    data = json.load(data_file)

web3 = Web3(HTTPProvider('http://localhost:8545'))
Verifier = web3.eth.contract(contract_name='Verifier', address=data['Verifier'],
                             abi=data['Verifier_abi'])

verify = Verifier.on('Verify')
verify.watch(verify_callback)

# web3.personal.unlockAccount(web3.eth.accounts[0], "123", 0)

# pr = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
# pub = pr.get_verifying_key()
# sig = pr.sign(message)

addr = web3.eth.accounts[0]
msg = 'lalalala'
# hex_msg = '0x' + msg.encode("hex")
hex_msg = msg
signature = web3.eth.sign(addr, hex_msg)

print("address -----> " + addr)
print("msg ---------> " + msg)
print("hex(msg) ----> " + hex_msg)
print("sig ---------> " + signature)

signature = signature[2:]
r = '0x' + signature[0:64]
s = '0x' + signature[64:128]
v = '0x' + signature[128:130]
v_decimal = web3.toDecimal(v)

print("r -----------> " + r)
print("s -----------> " + s)
print("v -----------> " + v)
print("vd ----------> " + str(v_decimal))

fixed_msg = "\x19Ethereum Signed Message:\n" + str(len(msg)) + msg
fixed_msg_sha = web3.sha3('0x' + msg.encode("hex"))
# fixed_msg_sha = web3.sha3(web3.fromAscii(fixed_msg)) #msg


print(fixed_msg_sha)
# data = Verifier.call().recoverAddr(fixed_msg_sha[:2], v_decimal, r[:2], s[:2])
data = Verifier.transact({'from': web3.eth.accounts[0]}).recoverAddr(fixed_msg_sha[:2], v_decimal, r[:2], s[:2])
print("-----data------")
print("input addr ==> " + addr)
print("output addr => " + data)


while True:
   pass
