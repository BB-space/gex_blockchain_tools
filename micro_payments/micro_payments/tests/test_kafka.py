import pytest
import json
import time


class Receiver:
    def __init__(self):
        self.list_messages = []
        self.dict_messages = []

    def add_message_list(self, message):
        self.list_messages.append(json.loads(message.value.decode('utf-8')))

    def add_message_dict(self, message=None, some_other_argument=None):
        assert some_other_argument == 'hello'
        self.dict_messages.append(json.loads(message.value.decode('utf-8')))


def test_main(create_sender, create_receiver):
    messages = [{'message': 'Hello World!'}, b'second', {'this': 'is sparta?'}]
    result = [{'message': 'Hello World!'}, {'this': 'is sparta?'}]
    r = Receiver()

    create_receiver.add_listener_function(r.add_message_list)
    create_receiver.add_listener_function(r.add_message_dict, args={'some_other_argument': 'hello'})
    thread = create_receiver.start()
    for message in messages:
        create_sender.send(message)
    time.sleep(5)
    create_receiver.stop()
    thread.join()
    assert result == r.list_messages
    assert result == r.dict_messages
