import logging
from gex_chain.utils import BalancesData
from micro_payments.channels.maintainer_channel import MaintainerChannel
from micro_payments.channels.channel import Channel
from micro_payments.kafka_lib.receiving_kafka import ReceivingKafka


log = logging.getLogger(__name__)


class ReceivingChannel(MaintainerChannel):
    """
    Channel used by the receiver
    """

    def __init__(
            self,
            client,
            sender: str,
            block: int,
            deposit=0,
            channel_fee=0,
            random_n=b'',
            balances_data=None,
            balances_data_sig=None,
            state=Channel.State.open,
            topic_holder=None,
            receiving_kafka: ReceivingKafka = None,
            my_balance: int = 0

    ):
        MaintainerChannel.__init__(
            self,
            client,
            sender,
            block,
            deposit,
            channel_fee,
            random_n,
            balances_data,
            balances_data_sig,
            state,
            topic_holder,
            receiving_kafka
        )
        self._my_balance = my_balance
        # create kafka channels

    @property
    def my_balance(self):
        return self._my_balance

    def set_new_balances(self, balances_data: BalancesData, balances_data_sig: bytes):
        value = super(self.__class__, self).set_new_balances(balances_data, balances_data_sig)  # TODO test
        if value:
            for pair in balances_data:
                if pair[0] == self.client.account:
                    self._my_balance = pair[1]
            return self.my_balance
        else:
            return None
