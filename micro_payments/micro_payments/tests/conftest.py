import pytest
from micro_payments.client import Client
from micro_payments.tests.config import signer_pass_path, signer_key_path


@pytest.fixture(scope='session')
def init_client(request):
    client = Client(key_path=signer_key_path, key_password_path=signer_pass_path)

    def finalizer():
        client.close()
    request.addfinalizer(finalizer)
    return client
