from web3 import HTTPProvider, Web3
import json
import time


def approval_callback(result):
    print("Approval")


def after_callback(result):
    print("After")


def transfer_callback(result):
    print("Transfer")


def ad_callback(result):
    print(result['args']['_owner'])


def before_callback(result):
    print("Before " + result['args']['_owner'])


with open('../data.json') as data_file:
    data = json.load(data_file)
web3 = Web3(HTTPProvider('http://localhost:8545'))
#c1 = web3.eth.contract(contract_name='c1', address=data['c1_address'], abi=data['c1_abi'])
#c2 = web3.eth.contract(contract_name='c2', address=data['c2_address'], abi=data['c2_abi'])
# print(c1.call().array())
# print(c2.call().get_array(data['c1_address']))
token = web3.eth.contract(contract_name='token', address=data['token_address'], abi=data['token_abi'])
t = web3.eth.contract(contract_name='t', address=data['t_address'], abi=data['t_abi'])
event_a = token.on('Approval')
event_a.watch(approval_callback)
event_t = token.on('Transfer')
event_t.watch(transfer_callback)
event_ad = token.on('Ad')
event_ad.watch(ad_callback)
before = t.on('Before')
before.watch(before_callback)
after = t.on('After')
after.watch(after_callback)
print(str(token.call().balanceOf(web3.eth.accounts[0])) + " " + str(token.call().balanceOf(web3.eth.accounts[1])))
web3.personal.unlockAccount(web3.eth.accounts[0], '123', 0)
#token.transact({'from': web3.eth.accounts[0]}).approve(data['token_address'], 200)
token.transact({'from': web3.eth.accounts[0]}).approve(data['t_address'], 200)
time.sleep(5)
t.transact({'from': web3.eth.accounts[0]}).bar(data['token_address'], web3.eth.accounts[0], web3.eth.accounts[1], 200)
time.sleep(7)
print(str(token.call().balanceOf(web3.eth.accounts[0])) + " " + str(token.call().balanceOf(web3.eth.accounts[1])))
