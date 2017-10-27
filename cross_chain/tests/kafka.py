import time
from micro_payments.kafka_lib.receiving_listener import ReceivingKafka
from micro_payments.kafka_lib.sender_kafka import SenderKafka
from threading import Thread

bootstrap_servers = ['10.1.0.56:9092']
topic = 'test'
group_id = 'group'
client_id = 'client'

sender = SenderKafka(topic, bootstrap_servers)
receiving = ReceivingKafka(topic, client_id, group_id, bootstrap_servers, lambda x: x)
receiving.add_listener_function(lambda x: print(x))
rec_thread = Thread(target=receiving.start)
rec_thread.start()

time.sleep(2)

sender.send(b'Hello World!')
sender.send(b'Can anybody hear me?')

time.sleep(10)

receiving.stop()
rec_thread.join()

print('Ended successfully')