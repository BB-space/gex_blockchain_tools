from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3


def check_successful_tx(web3: Web3, txid: str, timeout=180) -> dict:
    receipt = wait_for_transaction_receipt(web3, txid, timeout=timeout)
    txinfo = web3.eth.getTransaction(txid)
    # assert txinfo['gas'] != receipt['gasUsed']  # why does this work?
    return receipt
