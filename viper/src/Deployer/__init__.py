from time import sleep

from viper import compiler
from web3 import Web3, HTTPProvider


class Deployer:
    def __init__(self, web3_address, owner, owner_password):
        self.web3 = Web3(HTTPProvider(web3_address))
        self.web3.personal.unlockAccount(owner, owner_password, 0)
        self.owner = owner
        self.cmp = compiler.Compiler()
        self.wait_delta = 5
        self.wait_total = 120
        self.gas = 2500000

    def _get_contract_code(self, contract_path):
        contract = open(contract_path, 'r')
        contract_code = contract.read()
        contract.close()
        return contract_code

    def _compile_contract(self, contract_path):
        contract_code = self._get_contract_code(contract_path)
        contract_bytecode = self.cmp.compile(contract_code).hex()
        contract_abi = self.cmp.mk_full_signature(contract_code)
        return contract_bytecode, contract_abi

    def deploy(self, contract_path, params=None):
        print("Deploying contract: " + contract_path)
        if params is not None:
            print("Params: " + str(params))
        contract_bytecode, contract_abi = self._compile_contract(contract_path)
        contract = self.web3.eth.contract(contract_abi, bytecode=contract_bytecode)
        tx_hash = contract.deploy(args=params, transaction={'from': self.owner, 'gas': self.gas})
        i = 0
        while i < self.wait_total:
            try:
                sleep(self.wait_delta)
                tx_receipt = self.web3.eth.getTransactionReceipt(tx_hash)
                contract_address = tx_receipt['contractAddress']
                return contract_address, contract_abi
            except:
                i = i + self.wait_delta
        raise Exception("Contract deployment failed.")

    def wait_for_transaction(self, tx_hash):
        i = 0
        while i < self.wait_total:
            try:
                sleep(self.wait_delta)
                tx_receipt = self.web3.eth.getTransactionReceipt(tx_hash)
                return tx_receipt['gasUsed']
            except:
                i = i + self.wait_delta
        raise Exception("Transaction failed.")
