from contract_loader import ContractLoader
from listener import Listener


def event_callback(res):
    print("New Number: " + str(res['args']['name']))


contract = ContractLoader.get_contract('http://localhost:8545')

# listener = Listener.listen_for_event(contract, 'NewNumber')
# listener.watch(event_callback)
# listener.join()

past_events = Listener.past_event_filter(contract, 'NewNumber')
past_events.watch(event_callback)
past_events.join()

print(past_events)
