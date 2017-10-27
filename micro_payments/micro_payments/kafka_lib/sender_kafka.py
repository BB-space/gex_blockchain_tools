from kafka import KafkaProducer


class SenderKafka:
    def __init__(self,
                 topic: str,
                 bootstrap_servers):
        if isinstance(bootstrap_servers, str):
            bootstrap_servers = [bootstrap_servers]

        assert isinstance(bootstrap_servers, list)

        self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
        self.topic = topic

    def send(self, message, topic=None):
        if topic is None:
            topic = self.topic
        self.producer.send(topic, message)
        self.producer.flush()

