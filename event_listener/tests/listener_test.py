import logging
import unittest
import sys

sys.path.append('../')
from tests_helper import *

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ListenerTest(unittest.TestCase):
    def test_past_event_filter(self):
        try:
            contract = get_contract()
            Listener.past_event_filter(contract, 'NewNumber')
        except Exception:
            self.fail("past_event_filter() raised ExceptionType unexpectedly!")

    def test_event_filter(self):
        try:
            contract = get_contract()
            Listener.event_filter(contract, 'NewNumber')
        except Exception:
            self.fail("past_event_filter() raised ExceptionType unexpectedly!")


if __name__ == '__main__':
    unittest.main()
