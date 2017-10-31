from kafka import KafkaProducer
import logging
import json

log = logging.getLogger(__name__)


class SenderKafka:
    def __init__(self,
                 topic: str,
                 bootstrap_servers):
        if isinstance(bootstrap_servers, str):
            bootstrap_servers = [bootstrap_servers]

        assert isinstance(bootstrap_servers, list)

        self._producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
        self._closed = False
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers

    def send(self, message, topic=None):
        if self._closed:
            log.error('The sender is closed, create a new one to send a message')
            return None
        if topic is None:
            topic = self.topic
        if isinstance(message, dict):
            try:
                message = json.dumps(message)
            except ValueError:
                log.error('Could not convert {} to json string'.format(message))
                return None
        if isinstance(message, str):
            try:
                message = message.encode('utf-8')
            except ValueError:
                log.error('Could not convert {} to bytes'.format(message))
                return None
        if isinstance(message, bytes):
            log.debug('Sending {}'.format(message))
            result = self._producer.send(topic, message)
            self._producer.flush()
            return result
        else:
            log.error('The message must be either bytes, utf-8 string or a dict')
            return None

    def close(self):
        if not self._closed:
            self._closed = True
            self._producer.close()
