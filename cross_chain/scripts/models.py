import datetime
import peewee

database = peewee.SqliteDatabase('gex_blockchain.db')


class NodeEvents(peewee.Model):
    event_id = peewee.CharField(index=True)
    created_at = peewee.DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = database


class UserEvents(peewee.Model):
    event_id = peewee.CharField(index=True)
    created_at = peewee.DateTimeField(default=datetime.datetime.now)
    addr_from = peewee.CharField()
    addr_to = peewee.CharField()
    amount = peewee.IntegerField()
    is_gex_net = peewee.BooleanField()
    block_number = peewee.IntegerField()

    class Meta:
        database = database


def create_tables():
    database.connect()
    try:
        database.create_tables([NodeEvents, UserEvents], True)
    except Exception as e:
        print(str(e))
