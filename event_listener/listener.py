import logging
import json
from web3 import Web3, HTTPProvider

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Listener:

    @staticmethod
    def event_filter(contract_instance, event_name, filter_params=None, *callbacks):
        event_filter = contract_instance.on(event_name, filter_params, *callbacks)  # Todo *callbacks
        return event_filter

    @staticmethod
    def past_event_filter(contract_instance, event_name, filter_params=None, *callbacks):
        event_filter = contract_instance.pastEvents(event_name, filter_params, *callbacks)  # Todo *callbacks
        return event_filter
