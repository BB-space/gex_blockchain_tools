import logging
from copy import copy

from gex_chain.crypto import sign_balance_proof
from gex_chain.utils import convert_balances_data, check_overspend, BalancesData
from gex_chain.utils import get_data_for_token
from micro_payments.channels.channel import Channel, check_sign_with_logger

log = logging.getLogger(__name__)


class MaintainerChannel(Channel):
    """
    Channel used by the maintainer
    """

    @property
    def balances_data(self):
        return self._balances_data

    @balances_data.setter
    def balances_data(self, value: BalancesData):
        log.error('You cannot set new data in MaintainerChannel, use set_new_balances')
        return

    def _is_cheating(self, balance) -> bool:

        pass

    def _report_cheating(self, balances_data: BalancesData, balances_data_sig: bytes):
        if self.state == Channel.State.closed:
            log.error('Channel must not be closed to report cheating.')
            return None

        log.info('Reporting cheating to a channel created at block #{} by {} '.format(
            self.block, self.sender
        ))
        current_block = self.client.web3.eth.blockNumber

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'reportCheating',
            [
                self.sender,
                self.block,
                self.balances_data_converted,
                self.balance_sig,
                balances_data,
                balances_data_sig
            ]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for CheatingReported confirmation event...')
        event = self.client.channel_manager_proxy.get_cheating_reported_event_blocking(
            self.sender,
            self.block,
            current_block - 1
        )

        if event:
            log.info('Successfully reported cheating in block {}.'.format(event['blockNumber']))
            return event
        else:
            log.error('No event received.')
            return None

    @check_sign_with_logger(log)
    def set_new_balances(self, balances_data: BalancesData, balances_data_sig: bytes):
        if self._is_cheating(balances_data):
            self._report_cheating(balances_data, balances_data_sig)
        else:
            self._balances_data = balances_data
            self._balances_data_converted = convert_balances_data(balances_data)
            self._balances_data_sig = balances_data_sig

    def submit_later_transaction(self):
        if self.balances_data_converted is None:
            log.error('No data to send!')
            return None

        if self.state != Channel.State.settling:
            log.error('Channel must be in settlement period to submit a later transfer.')
            return None

        log.info('Sending a new transaction to a channel created at block #{} by {} '.format(
            self.block, self.sender
        ))
        current_block = self.client.web3.eth.blockNumber

        tx = self.client.channel_manager_proxy.create_signed_transaction(
            'submitLaterTransaction', [self.sender, self.block, self.balances_data_converted, self.balance_sig]
        )
        self.client.web3.eth.sendRawTransaction(tx)

        log.info('Waiting for ClosingBalancesChanged confirmation event...')
        event = self.client.channel_manager_proxy.get_channel_closing_balances_changed_event_blocking(
            self.sender,
            self.block,
            current_block - 1
        )

        if event:
            log.info('Successfully submitted new transaction in block {}.'.format(event['blockNumber']))
            return event
        else:
            log.error('No event received.')
            return None