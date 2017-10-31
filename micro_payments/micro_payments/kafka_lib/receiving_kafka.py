from kafka import KafkaConsumer
from threading import Thread
from copy import deepcopy
import json
from json import JSONDecodeError
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
        self.bootstrap_servers = bootstrap_servers
        self.listeners = []
        self._stopped = False
        self._running = False

    def add_listener_function(self, f, filters: dict = None, args=None) -> bool:
        if filters is None:
            filters = {}
        if self._stopped or self._running:
            return False
        if args is None:
            args = []

        self.listeners.append([f, args, filters])
        return True

    def start(self):
        if self._stopped or self._running:
            return None
        else:
            self._running = True
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
                    self.handle_message(message)

        except (ValueError, OSError) as error:
            if self._stopped:
                return
            else:
                raise error

    def _helper(self, listener, message):
        new_args = add_message(listener[1], message)
        if isinstance(new_args, list):
            Thread(target=listener[0], args=new_args, daemon=True).start()
        elif isinstance(new_args, dict):
            Thread(target=listener[0], kwargs=new_args, daemon=True).start()

    def handle_message(self, message):
        try:
            message_value = json.loads(message.value)
        except JSONDecodeError:
            log.warning('The message {} is not json encoded, skipping'.format(message))
            return
        for listener in self.listeners:
            listener_filter = listener[2]
            if listener_filter == {}:
                self._helper(listener, message)
            else:
                for key in listener_filter.keys():
                    try:
                        if listener_filter[key] == message_value[key]:
                            self._helper(listener, message)
                            break
                    except KeyError:
                        pass

    def stop(self):
        if self._running and not self._stopped:
            self._stopped = True
            self._running = False
            self._consumer.close()
