from web3 import Web3, HTTPProvider
from ecdsa import SigningKey, SECP256k1
import sign
import sha3
import binascii
import json
from ethereum.utils import encode_hex


priv_keys = []
addresses = []
TEST_AMOUNT = 3


# Creates a new priv_key / address pair. Does not create a wallet using geth. All the info is stored in memory
def create_wallet():
    keccak = sha3.keccak_256()
    priv = SigningKey.generate(curve=SECP256k1)
    pub = priv.get_verifying_key().to_string()
    keccak.update(pub)
    address = keccak.hexdigest()[24:]
    return (encode_hex(priv.to_string()), address)


def get_data():
    with open('data.json') as data_file:
        data = json.load(data_file)
    return data


def create_wallets():
    global priv_keys
    global addresses
    for i in range(TEST_AMOUNT):
        priv_key, address = create_wallet()
        priv_keys.append(priv_key)
        addresses.append('0x' + address)


def check_for_message(message, verifier):
    for i in range(TEST_AMOUNT):
        message_sig, sig_address = sign.check(message, binascii.unhexlify(priv_keys[i]))
        message_hex = sign.eth_message_hex(message)
        r = message_sig[0:32]
        s = message_sig[32:64]
        v = int(message_sig[64]) + 27
        print(r)
        print(s)
        print(v)
        data = verifier.call().recoverAddr(message_hex, v, r, s)
        print('{} - signer, {} - got'.format(addresses[i], data))


if __name__ == '__main__':
    web3 = Web3(HTTPProvider('http://localhost:8545'))

    data = get_data()
    owner = web3.eth.accounts[0]
    my_verifier = web3.eth.contract(contract_name='Verifier', address=data['Verifier'],
                                 abi=data['Verifier_abi'])
    create_wallets()
    message = 'Hello World!'
    check_for_message(message, my_verifier)
