import os
from eth_utils import denoms
from web3 import HTTPProvider

API_PATH = "/api/1"
GAS_LIMIT = 2500000
GAS_PRICE = 20 * denoms.gwei

NETWORK_NAMES = {
    1: 'mainnet',
    2: 'morden',
    3: 'ropsten',
    4: 'rinkeby',
    30: 'rootstock-main',
    31: 'rootstock-test',
    42: 'kovan',
    61: 'etc-main',
    62: 'etc-test',
    1337: 'geth'
}


CHANNEL_MANAGER_ADDRESS = '0x99f2dce01ab0e19ce2a9fa39b52e9c9a99c1f6d6'
TOKEN_ADDRESS = '0xcc3197d2be2e5c048b183ae0c2f6154df10db08a'  # 0x437d949b36b8C25f7cba46bA55F071852060335a

WEB3_PROVIDER = HTTPProvider("http://127.0.0.1:8545", request_kwargs={'timeout': 60})
