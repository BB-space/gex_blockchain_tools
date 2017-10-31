from micro_payments.event_listener.listener import Listener


class MainListener(Listener):
    def __init__(self, contract):
        Listener.__init__(self)
        self.contract = contract

    def start(self):
        pass
