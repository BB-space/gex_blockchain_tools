import json
import time

import numpy as np
from web3 import HTTPProvider, Web3

size = 4
arr = [[-1] * size, [-1] * size]
for i in range(3, size * 5 + 3):
    if i >= size*2 and i % size == 0:
        for j in range(0, size):
            arr[int(i % (size * 2) / size)] [j] = -1
    arr[int(i % (size*2) / size)][(i % (size*2)) % size] = i
    print(i)
    print(arr[0])
    print(arr[1])

'''
# i > 2
#odd
size = 4
arr = [[-1] * size, [-1] * size]
for i in range(0, size * 7 + 1):
    if i-1 > size and i % size == 0:
        for j in range(i % size, size):
            arr[(i+j) % 2][j % size] = -1
    arr[i % 2][i % size] = i
    if i % size == 0:
        print(i)
        print(arr[0])
        print(arr[1])


arr = [[0] * 256, [0] * 256]
for i in range(1,258):
    if i > 256 and (i-1)%256 == 0:
        arr[(i-1) % 2] = [0] * 256
    arr[(i-1)%2][(i-1) % 256] = i
    print(i)
    print(arr[0])
print(arr[1])
'''
'''
with open('../data.json') as data_file:
    data = json.load(data_file)
web3 = Web3(HTTPProvider('http://localhost:8545'))
contract = web3.eth.contract(contract_name='Registration', address=data['registration_address'],
                             abi=data['registration_abi'])

contract.transact({'from': web3.eth.accounts[0]}).setNumber(2)
time.sleep(30)
callData = contract.call().test();
gasEstimate = web3.eth.estimateGas({ 'from': web3.eth.accounts[0], 'to': data['registration_address'], 'value': callData})
print(gasEstimate)
contract.transact({'from': web3.eth.accounts[0]}).setNumber(19999)
time.sleep(30)
#print(contract.call().test())

callData = contract.call().test();
gasEstimate = web3.eth.estimateGas({ 'from': web3.eth.accounts[0], 'to': data['registration_address'], 'value': callData})
print(gasEstimate)
'''