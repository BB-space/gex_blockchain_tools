from micro_payments.deploy.config import D160, private_keys, addresses, SENDERS, FILE_PATH
from web3.utils.compat import Timeout
from ethereum.utils import encode_hex
import json
from ecdsa import SigningKey, SECP256k1
import sha3

def generate_data(amounts, address_list=addresses):
    data = []
    for i in range(len(amounts)):
        data.append(D160 * amounts[i] + int(address_list[i], 0))
    return data


def generate_wallets():
    for i in range(SENDERS - 1):
        priv_key, address = create_wallet()
        private_keys.append(priv_key)
        addresses.append('0x' + address)


def create_wallet():
    keccak = sha3.keccak_256()
    priv = SigningKey.generate(curve=SECP256k1)
    pub = priv.get_verifying_key().to_string()
    keccak.update(pub)
    address = keccak.hexdigest()[24:]
    return encode_hex(priv.to_string()), address


def write_to_file(**kwargs):
    path = kwargs.pop('file_path', FILE_PATH)
    with open(path, 'w') as data_file:
        json.dump(kwargs, data_file)


def read_from_file():
    with open(FILE_PATH) as data_file:
        data = json.load(data_file)
    return data


def wait(transfer_filter, timeout=30):
    with Timeout(timeout) as timeout:
        while not transfer_filter.get(False):
            timeout.sleep(2)
