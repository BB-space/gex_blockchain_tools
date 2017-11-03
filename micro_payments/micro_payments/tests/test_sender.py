import time
import pytest


def test_create_channel(create_client):
    assert create_client.open_channel(50000, 333)


def test_create_transfer(create_client):
    assert create_client.sender_channel.create_transfer(
        [(create_client.web3.eth.accounts[1], create_client.sender_channel.deposit - 100)]
    )
    assert create_client.channel_manager_proxy.contract.call().verifyBalanceProof(
        create_client.web3.eth.accounts[0],
        create_client.sender_channel.block,
        create_client.sender_channel.balances_data_converted,
        create_client.sender_channel.balance_sig
    )


def test_top_up_channel(create_client):
    assert create_client.sender_channel.top_up(5000)


def test_close_channel(create_client):
    time.sleep(20)
    assert create_client.sender_channel.close()


def test_settle_channel(create_client):
    time.sleep(20)
    assert create_client.sender_channel.settle()
