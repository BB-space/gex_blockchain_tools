import pytest
import time


class Receiver:
    def __init__(self):
        self.list_messages = []
        self.dict_messages = []

    def add_message_list(self, message):
        self.list_messages.append(message.value)

    def add_message_dict(self, message=None, some_other_argument=None):
        assert some_other_argument == 'hello'
        self.dict_messages.append(message.value)


def test_main(create_sender, create_receiver):
    messages = [b'first', b'second', b'third']
    r = Receiver()

    create_receiver.add_listener_function(r.add_message_list)
    create_receiver.add_listener_function(r.add_message_dict, {'some_other_argument': 'hello'})
    thread = create_receiver.start()
    for message in messages:
        create_sender.send(message)
    time.sleep(2)
    create_receiver.stop()
    thread.join()
    assert messages == r.list_messages
    assert messages == r.dict_messages
