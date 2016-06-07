from contextlib import contextmanager
import os
import random
import string
import unittest

from trip_planner import utils

def random_string(length=10, prefix='', suffix=''):
    chars = string.ascii_lowercase + string.digits
    s = ''.join(random.choice(chars) for _ in range(length))
    return prefix + s + suffix

@contextmanager
def temp_database(db_name=None):
    db_name = db_name or random_string(prefix='/tmp/db-', suffix='.sql')
    engine = utils.database_engine(db_name)
    try:
        yield engine
    finally:
        os.remove(db_name)

class BaseTestClient(unittest.TestCase): #pylint: disable=too-many-public-methods

    def assert_dictionary(self, obj, skip=[]): #pylint: disable=dangerous-default-value
        if not isinstance(obj, list):
            obj_list = [obj]
        else:
            obj_list = obj
        for obj in obj_list:
            for key, value in obj.items():
                if key in skip:
                    continue
                self.assertNotEqual(value, None)

    def assertLength(self, item, length):
        self.assertEqual(len(item), length)
