import os
import logging
from populus import Project

from gex_chain.populus_utils import check_successful_tx
from micro_payments.deploy.utils import write_to_file
from micro_payments.deploy.config import \
    FILE_PATH, CHAIN_NAME, txn_wait, token_name, challenge_period, channel_lifetime


def deploy_contracts():
    if os.path.isfile(FILE_PATH) and \
                    os.path.getmtime(FILE_PATH) > os.path.getmtime('../../contracts/MicroTransferChannels.sol'):
        return

    logging.info('Deploying new contracts')
    project = Project()
    with project.get_chain(CHAIN_NAME) as chain:
        web3 = chain.web3
        owner = web3.eth.accounts[0]
        print(chain.provider)

        token_factory = chain.provider.get_contract_factory('GEXToken')  # This will be the abi of the token
        tx_hash = token_factory.deploy(transaction={'from': owner})  # the way we deploy contracts
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        token_address = receipt['contractAddress']
        logging.info('{} address is {}'.format(token_name, token_address))

        channel_factory = chain.provider.get_contract_factory('MicroTransferChannels')
        tx_hash = channel_factory.deploy(
            args=[token_address, challenge_period, channel_lifetime],
            transaction={'from': owner}
        )
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        channels_address = receipt['contractAddress']
        logging.info('MicroTransferChannels address is {}'.format(channels_address))

        node_factory = chain.provider.get_contract_factory('NodeContract')
        tx_hash = node_factory.deploy(transaction={'from': owner})
        receipt = check_successful_tx(chain.web3, tx_hash, txn_wait)
        node_address = receipt['contractAddress']
        logging.info('NodeContract address is {}'.format(node_address))

        tx_hash = node_factory(node_address).transact({'from': owner}).addNode(owner, '10.1.0.56', 1337, 'public_key')
        check_successful_tx(chain.web3, tx_hash, txn_wait)

    write_to_file(
        channels_abi=channel_factory.abi,
        token_abi=token_factory.abi,
        node_abi=node_factory.abi,
        token_address=token_address,
        channels_address=channels_address,
        node_address=node_address
    )
    print('Deployed')


if __name__ == '__main__':
    deploy_contracts()
