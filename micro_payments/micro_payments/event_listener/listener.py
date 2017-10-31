
class Listener:
    def __init__(self):
        self._stopped = False
        self._filters = []

    def stop(self):
        self._stopped = True
        for filter_ in self._filters:
            filter_.stop_watching()

    def _listener_decorator(self, f):

        def decorated(*args, **kwargs):
            if self._stopped:
                return None
            return f(*args, **kwargs)

        return decorated

    def add_listener(self, contract,  event_name, filter_params=None, *callbacks):
        callbacks = [self._listener_decorator(f) for f in callbacks]
        event_filter = contract.on(event_name, filter_params, *callbacks)
        self._filters.append(event_filter)
        return event_filter
