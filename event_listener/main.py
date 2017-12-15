from contract_loader import ContractLoader
from listener import Listener


def event_callback(res):
    print("New Number: " + str(res['args']['name']))


contract = ContractLoader.get_contract('http://localhost:8545')

listener = Listener.listen_for_event(contract, 'NewNumber')
listener.watch(event_callback)
listener.join()
