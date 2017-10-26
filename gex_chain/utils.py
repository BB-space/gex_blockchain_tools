import os
import stat
import json
import getpass
import logging
from ethereum import keys
from eth_utils import (
    decode_hex,
    encode_hex,
    is_hex,
)
from typing import List, Tuple

Address = str
Balance = int
BalancesData = List[Tuple[Address, Balance]]
BalancesDataConverted = List[int]
D160 = 2 ** 160


log = logging.getLogger(__name__)


def get_data_for_token(first_byte: int, last_bytes: int) -> bytes:
    data_bytes = (first_byte).to_bytes(5, byteorder='little')
    data_int = int.from_bytes(data_bytes, byteorder='big') + last_bytes
    data_bytes = (data_int).to_bytes(5, byteorder='big')
    return data_bytes


def convert_balances_data(balances_data: BalancesData) -> BalancesDataConverted:
    data = []
    for pair in balances_data:
        data.append(D160 * pair[1] + int(pair[0], 0))
    return data


def check_overspend(deposit: int, balances_data: BalancesData) -> Tuple[bool, int]:
    for pair in balances_data:
        deposit -= pair[1]
    return deposit < 0, deposit


def parse_balance_proof_msg(proxy, receiver, open_block_number, balance, signature):
    return proxy.verifyBalanceProof(receiver, open_block_number, balance, signature)


def check_permission_safety(path):
    """Check if the file at the given path is safe to use as a state file.

    This checks that group and others have no permissions on the file and that the current user is
    the owner.
    """
    f_stats = os.stat(path)
    return (f_stats.st_mode & (stat.S_IRWXG | stat.S_IRWXO)) == 0 and f_stats.st_uid == os.getuid()


def get_private_key(key_path, password_path=None):
    """Open a JSON-encoded private key and return it

    If a password file is provided, uses it to decrypt the key. If not, the
    password is asked interactively. Raw hex-encoded private keys are supported,
    but deprecated."""

    assert key_path, key_path
    if not os.path.exists(key_path):
        log.fatal("%s: no such file", key_path)
        return None

    if not check_permission_safety(key_path):
        log.fatal("Private key file %s must be readable only by its owner.", key_path)
        return None

    if password_path and not check_permission_safety(password_path):
        log.fatal("Password file %s must be readable only by its owner.", password_path)
        return None

    with open(key_path) as keyfile:
        private_key = keyfile.readline().strip()

        if is_hex(private_key) and len(decode_hex(private_key)) == 32:
            log.warning("Private key in raw format. Consider switching to JSON-encoded")
        else:
            keyfile.seek(0)
            try:
                json_data = json.load(keyfile)
                if password_path:
                    with open(password_path) as password_file:
                        password = password_file.readline().strip()
                else:
                    password = getpass.getpass("Enter the private key password: ")
                private_key = encode_hex(keys.decode_keystore_json(json_data, password))
            except:
                log.fatal("Invalid private key format or password!")
                return None

    return private_key
