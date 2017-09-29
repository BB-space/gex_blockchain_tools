from web3 import Web3, HTTPProvider
import json

web3 = Web3(HTTPProvider('http://localhost:8545'))
abi = '[{"constant":false,"inputs":[{"name":"_value","type":"int256"}],"name":"foo","outputs":[{"name":"","type":"int256"}],"payable":false,"type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":false,"name":"_value","type":"int256"}],"name":"ReturnValue","type":"event"}]'

contract = web3.eth.contract(contract_name='ExampleContract', address='0x484d58afbe4950b4020db10f4b83b6e71f4604a2',abi=json.loads(abi))


def my_callback(log):
    print(log)
    print
    print(log['args'])
    pass


funded_filter = contract.on('ReturnValue')
#past_filter = contract.pastEvents('Invested')
#print(past_filter.get())
funded_filter.watch(my_callback)

print "send"
#web3.personal.unlockAccount(web3.eth.accounts[0], '123');
#web3.eth.coinbase
contract.transact({'from': web3.eth.accounts[1]}).foo(55555555)
while True:
    pass
