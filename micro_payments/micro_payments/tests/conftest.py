import pytest
from micro_payments.client import Client
from micro_payments.tests.config import signer_pass_path, signer_key_path
from micro_payments.kafka_lib.sender_kafka import SenderKafka
from micro_payments.kafka_lib.receiving_kafka import ReceivingKafka


bootstrap_servers = ['localhost:9092']
topic = 'test'
group_id = 'group'
client_id = 'client'


@pytest.fixture(scope='session')
def create_client(request):
    client = Client(key_path=signer_key_path, key_password_path=signer_pass_path)

    def finalizer():
        client.close()
    request.addfinalizer(finalizer)
    return client


@pytest.fixture('module')
def create_sender(request):
    sender = SenderKafka(topic, bootstrap_servers)

    def finalizer():
        sender.close()

    request.addfinalizer(finalizer)
    return sender


@pytest.fixture('module')
def create_receiver(request):
    receiver = ReceivingKafka(topic, client_id, group_id, bootstrap_servers)

    def finalizer():
        receiver.stop()

    request.addfinalizer(finalizer)
    return receiver