import time
import pytest


def test_create_channel(init_client):
    assert init_client.open_channel(50000, 333)


def test_create_transfer(init_client):
    assert init_client.sender_channel.create_transfer([(init_client.web3.eth.accounts[1], init_client.sender_channel.deposit - 100)])
    assert init_client.channel_manager_proxy.contract.call().verifyBalanceProof(
        init_client.web3.eth.accounts[0],
        init_client.sender_channel.block,
        init_client.sender_channel.balances_data_converted,
        init_client.sender_channel.balance_sig
    )


def test_top_up_channel(init_client):
    assert init_client.sender_channel.top_up(5000)


def test_close_channel(init_client):
    time.sleep(20)
    assert init_client.sender_channel.close()


def test_settle_channel(init_client):
    time.sleep(20)
    assert init_client.sender_channel.settle()
