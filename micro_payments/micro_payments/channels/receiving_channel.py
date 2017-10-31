import logging
from gex_chain.utils import convert_balances_data, check_overspend, BalancesData, is_cheating
from micro_payments.channels.maintainer_channel import MaintainerChannel
from micro_payments.channels.channel import Channel, check_sign_with_logger
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
            state,
            topic_holder,
            receiving_kafka
        )
        self._my_balance = my_balance
        # create kafka channels

    @property
    def my_balance(self):
        return self._my_balance

    @check_sign_with_logger(log)
    def set_new_balances(self, balances_data: BalancesData, balances_data_sig: bytes):
        cheating = self._is_cheating(balances_data)
        if cheating is None:
            log.error('Got wrong new balances data (probably wrong order)')
            return
        if cheating:
            self._report_cheating(balances_data, balances_data_sig)
        else:
            self._balances_data = balances_data
            self._balances_data_converted = convert_balances_data(balances_data)
            self._balances_data_sig = balances_data_sig
            for pair in balances_data:
                if pair[0] == self.client.account:
                    self._my_balance = pair[1]

        return self.my_balance
