import pytest
import time


class Receiver:
    def __init__(self):
        self.messages = []

    def add_message(self, message):
        self.messages.append(message.value)


def test_main(create_sender, create_receiver):
    messages = [b'first', b'second', b'third']
    r = Receiver()

    create_receiver.add_listener_function(r.add_message)
    thread = create_receiver.start()
    for message in messages:
        create_sender.send(message)
    time.sleep(2)
    create_receiver.stop()
    thread.join()
    assert messages == r.messages
