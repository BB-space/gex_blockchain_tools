import time
from contract_loader import ContractLoader
from listener import Listener


def event_callback(res):
    print("New Number: " + str(res['args']['name']))


contract = ContractLoader.get_contract('http://localhost:8545')

listeners = {
    'NewNumber': Listener.event_filter(contract, 'NewNumber')
}
listeners['NewNumber'].watch(event_callback)

while True:
    time.sleep(5)
    print('check')
# listener.join()


# past_events = Listener.past_event_filter(contract, 'NewNumber')
# past_events.watch(event_callback)
# past_events.join()

# print(past_events)
