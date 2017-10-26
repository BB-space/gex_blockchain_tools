import pytest
import time
from micro_payments.sender.client import Client


signer_key_path = "/tmp/ethereum_dev_mode/keystore/UTC--2017-10-13T07-47-42.456207242Z" \
                  "--f43b2675fc72ce6e48f7063dcf0ee74ad04d40ff"
signer_pass_path = '/tmp/ethereum_dev_mode/keystore/f43b2675fc72ce6e48f7063dcf0ee74ad04d40ff'


@pytest.fixture(scope='module')
def init_client(request):
    client = Client(key_path=signer_key_path, key_password_path=signer_pass_path)

    def finalizer():
        client.close()
    request.addfinalizer(finalizer)
    return client


def test_create_channel(init_client):
    assert init_client.open_channel(50000, 333)


def test_create_transfer(init_client):
    print([(init_client.web3.eth.accounts[1], init_client.channel.deposit - 100)])
    assert init_client.channel.create_transfer([(init_client.web3.eth.accounts[1], init_client.channel.deposit - 100)])
    assert init_client.channel_manager_proxy.contract.call().verifyBalanceProof(
        init_client.web3.eth.accounts[0],
        init_client.channel.block,
        init_client.channel.balances_data_converted,
        init_client.channel.balance_sig
    )


def test_top_up_channel(init_client):
    assert init_client.channel.top_up(5000)


def test_close_channel(init_client):
    time.sleep(20)
    assert init_client.channel.close()


def test_settle_channel(init_client):
    time.sleep(20)
    assert init_client.channel.settle()
