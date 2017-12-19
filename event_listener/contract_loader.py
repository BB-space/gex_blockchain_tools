import logging
import json
from web3 import Web3, HTTPProvider
import os

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ContractLoader:
    @staticmethod
    def get_contract(web3_host):
        contract_data = ContractLoader.get_contract_data()
        return ContractLoader.get_contract_instance(web3_host, contract_data['registration_address'],
                                                    contract_data['registration_abi'])

    # todo load from ?
    @staticmethod
    def get_contract_data():
        path = ContractLoader.get_contract_path()
        logger.info('Loading contract data from `{0}`'.format(path))
        with open(path) as data_file:
            return json.load(data_file)

    @staticmethod
    def get_contract_instance(web3_host, contract_address, contract_abi):
        assert web3_host.startswith('http://')
        web3 = Web3(HTTPProvider(web3_host))
        return web3.eth.contract(contract_name='TestContract', address=contract_address,
                                 abi=contract_abi)

    @staticmethod
    def get_contract_path():
        if os.path.exists('../viper/data.json'):
            path = '../viper/data.json'
        elif os.path.exists('../../viper/data.json'):
            path = '../../viper/data.json'
        else:
            raise FileNotFoundError('`data.json` not found')
        return path
