from kafka import KafkaConsumer
from threading import Thread
from copy import deepcopy
import json
import logging

log = logging.getLogger(__name__)


def add_message(args, message):
    if isinstance(args, list):
        new_args = deepcopy(args)
        new_args.append(message)
        return new_args
    if isinstance(args, dict):
        new_kwargs = deepcopy(args)
        new_kwargs['message'] = message
        return new_kwargs


class ReceivingKafka:
    def __init__(self,
                 topic: str,
                 client_id: str,
                 group_id: str,
                 bootstrap_servers,
                 value_deserializer=lambda x: x
                 ):
        if isinstance(bootstrap_servers, str):
            bootstrap_servers = [bootstrap_servers]

        assert isinstance(bootstrap_servers, list)

        self.topic = topic
        self._consumer = KafkaConsumer(
            topic,
            client_id=client_id,
            group_id=group_id,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=value_deserializer
        )
        self.listeners = []
        self._stopped = False

    def add_listener_function(self, f, args=None) -> bool:
        if args is None:
            args = []
        if self._stopped:
            return False

        self.listeners.append([f, args])
        return True

    def start(self):
        thread = Thread(target=self.run)
        thread.start()
        return thread

    def run(self):
        try:
            for message in self._consumer:
                if message is None:
                    log.warning('Got message of type None')
                else:
                    log.debug('Got message: {}'.format(message))
                    for listener in self.listeners:
                        new_args = add_message(listener[1], message)
                        if isinstance(new_args, list):
                            Thread(target=listener[0], args=new_args).start()
                        elif isinstance(new_args, dict):
                            Thread(target=listener[0], kwargs=new_args).start()

        except (ValueError, OSError) as error:
            if self._stopped:
                return
            else:
                raise error

    def stop(self):
        if not self._stopped:
            self._stopped = True
            self._consumer.close()
