from kafka import KafkaConsumer
from threading import Thread
import json


class ReceivingKafka:
    def __init__(self,
                 topic: str,
                 client_id: str,
                 group_id: str,
                 bootstrap_servers,
                 value_deserializer=lambda m: json.loads(m.decode('ascii'))
                 ):
        if isinstance(bootstrap_servers, str):
            bootstrap_servers = [bootstrap_servers]

        assert isinstance(bootstrap_servers, list)

        self.topic = topic
        self.consumer = KafkaConsumer(
            topic,
            client_id=client_id,
            group_id=group_id,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=value_deserializer
        )
        self.listeners = []

    def add_listener_function(self, f):
        self.listeners.append(f)

    def start(self):
        try:
            for message in self.consumer:
                for listener in self.listeners:
                    Thread(target=listener, args=[message]).start()
        except ValueError:
            return

    def stop(self):
        self.consumer.close()
