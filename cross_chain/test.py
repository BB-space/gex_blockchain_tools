from web3 import Web3, HTTPProvider
import json
import time

with open('data.json') as data_file:
    data = json.load(data_file)

web3 = Web3(HTTPProvider('http://localhost:8545'))
gexContract = web3.eth.contract(contract_name='GexContract', address=data['GexContract'],
                                abi=data['GexContract_abi'])
web3.personal.unlockAccount(web3.eth.accounts[0], "123", 0)

l = "lala"
val = l
# val = web3.toBytes(l)
print val
gexContract.transact({'from': web3.eth.accounts[0]}).add(val)

print gexContract.call().getValidators(val)
print gexContract.call().getAmount(val)
time.sleep(10)
g = gexContract.call().getValidators(val)
print gexContract.call().getAmount(val)
for gg in g:
    print gg
