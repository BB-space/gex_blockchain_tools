import logging

log = logging.getLogger(__name__)


class Listener:
    def __init__(self):
        self._stopped = False
        self._filters = []

    @property
    def stopped(self):
        return self._stopped

    def stop(self):
        self._stopped = True
        for filter_ in self._filters:
            filter_.stop_watching()
            # TODO test this
            try:
                filter_.kill()
            except Exception as ex:
                log.warning(ex)

    def _listener_decorator(self, f):

        def decorated(*args, **kwargs):
            if self._stopped:
                return None
            return f(*args, **kwargs)

        return decorated

    def listen_for_event(self, contract, event_name, filter_params=None, *callbacks):
        callbacks = [self._listener_decorator(f) for f in callbacks]
        event_filter = contract.on(event_name, filter_params, *callbacks)
        self._filters.append(event_filter)
        return event_filter


def _get_listener(contract, event_name, filter_params=None, *callbacks):
    listener = Listener()
    listener.listen_for_event(contract, event_name, filter_params, *callbacks)
    return listener


def listen_for_channel_creation(contract, filter_params=None, *callbacks):
    return _get_listener(contract, 'ChannelCreated', filter_params, *callbacks)


def listen_for_channel_closing(contract, filter_params, *callbacks):
    return _get_listener(contract, 'ChannelCloseRequested', filter_params, *callbacks)


def listen_for_topic_creation(contract, filter_params, *callbacks):
    return _get_listener(contract, 'ChannelTopicCreated', filter_params, *callbacks)


def listen_for_balances_change(contract, filter_params, *callbacks):
    return _get_listener(contract, 'ClosingBalancesChanged', filter_params, *callbacks)


def listen_for_channel_settle(contract, filter_params, *callbacks):
    return _get_listener(contract, 'ChannelSettled', filter_params, *callbacks)


def listen_for_cheating_report(contract, filter_params, *callbacks):
    return _get_listener(contract, 'CheatingReported', filter_params, *callbacks)


def listen_for_channel_top_up(contract, filter_params, *callbacks):
    return _get_listener(contract, 'ChannelToppedUp', filter_params, *callbacks)


def listen_for_maintainer_registration(contract, filter_params, *callbacks):
    return _get_listener(contract, 'MaintainerRegistered', filter_params, *callbacks)
