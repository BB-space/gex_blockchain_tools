import logging
import json
from web3 import Web3, HTTPProvider

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Listener:
    def __init__(self):
        self._stopped = False

    @staticmethod
    def listen_for_event(contract_instance, event_name, filter_params=None, *callbacks):
        event_filter = contract_instance.on(event_name, filter_params, *callbacks)  # Todo *callbacks
        return event_filter

    @staticmethod
    def past_event_filter(contract_instance, event_name, filter_params=None, *callbacks):
        event_filter = contract_instance.pastEvents(event_name, filter_params, *callbacks)  # Todo *callbacks
        return event_filter

#
# with open('../viper/data.json') as data_file:
#     contract_data = json.load(data_file)
#
# web3 = Web3(HTTPProvider('http://localhost:8545'))
# contract = web3.eth.contract(contract_name='TestContract', address=contract_data['registration_address'],
#                              abi=contract_data['registration_abi'])
#
#
# def event_callback(res):
#     log.info("Event caught")
#     print("New Number: " + str(res['args']['name']))
#
#
# events = Listener.listen_for_event(contract, 'NewNumber')
# events.watch(event_callback)
#
# events.join()
