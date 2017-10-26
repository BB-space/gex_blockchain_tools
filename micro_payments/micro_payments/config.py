import os
import json
import click
from eth_utils import denoms

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

APP_FOLDER = click.get_app_dir('Micro Payments', force_posix=True)
DATA_FILE_NAME = 'data.json'
