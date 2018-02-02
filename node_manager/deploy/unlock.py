from populus import Project

try:
    from .config import *
except SystemError:
    from config import *

print("Unlocking account[0]")
project = Project()
with project.get_chain(TEST_CHAIN_NAME) as chain:
    web3 = chain.web3
    if not web3.eth.accounts:
        web3.personal.importRawKey('3b403794d39dc13a41703f2cb6d6704119c7e38c024f97cce33db07eb4afe671', '11111111')
    owner = web3.eth.accounts[0]
    web3.personal.unlockAccount(owner, '11111111')
    print("Unlocked")