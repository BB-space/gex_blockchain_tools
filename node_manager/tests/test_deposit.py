import json
from web3 import HTTPProvider, Web3

with open('../../data.json') as data_file:
    data = json.load(data_file)
web3 = Web3(HTTPProvider("http://51.0.1.99:8545"))
contract = web3.eth.contract(contract_name='NodeManager', address=data['node_manager_address'], abi=data['node_manager_abi'])

ip = "255.255.255.255"
port = 6000
nonce = 12345

def get_data_for_token(first_byte, last_bytes) -> bytes:
    data_bytes = first_byte.to_bytes(5, byteorder='little')
    data_int = int.from_bytes(data_bytes, byteorder='big') + last_bytes
    data_bytes = data_int.to_bytes(5, byteorder='big')
    return data_bytes

print(contract.call().fallbackDataConvert(port.to_bytes(4, byteorder='big')+nonce.to_bytes(4, byteorder='big')+ip.encode()))

