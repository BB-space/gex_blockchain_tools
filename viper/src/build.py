from time import sleep

from web3 import Web3, HTTPProvider
from viper import compiler
from web3.contract import ConciseContract
import sys

# import eth-testrpc
example_contract = open(sys.argv[1], 'r')
contract_code = example_contract.read()
example_contract.close()

cmp = compiler.Compiler()
contract = cmp.compile(contract_code).hex()
contract_abi = cmp.mk_full_signature(contract_code)

web3 = Web3(HTTPProvider('http://10.1.0.11:8545'))
print(web3.personal.unlockAccount(web3.eth.accounts[0], '123', 0)) #true

# Instantiate and deploy contract
contract = web3.eth.contract(contract_abi, bytecode=contract)

# Get transaction hash from deployed contract
# tx_hash = contract.deploy(transaction={'from': web3.eth.accounts[0], 'gas': 410000},
#                           kwargs=({'_company': '0x866F092fceE4d850EdEaFa9Ff5DD18F40840fadf', '_total_shares': 10,
#                                    'initial_price': 10000}))

tx_hash = contract.deploy(transaction={'from': web3.eth.accounts[0], 'gas': 410000})
sleep(7)

# Get tx receipt to get contract address
tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
contract_address = tx_receipt['contractAddress']

# Contract instance in concise mode
contract_instance = web3.eth.contract(contract_abi, contract_address, ContractFactoryClass=ConciseContract)


print(str(contract_abi).replace("'", "\"").replace("True", "true").replace("False", "false"))
print(contract_address)
# Getters + Setters for web3.eth.contract object
#print('Contract value: {}'.format(contract_instance.received()))