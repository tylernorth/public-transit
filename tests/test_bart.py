from datetime import datetime
import httpretty
import unittest

from transit import client
from transit.exceptions import TransitException
from transit.urls import bart

from tests.data.bart import bsa
from tests.data.bart import train_count
from tests.data.bart import elevator

class TestClient(unittest.TestCase):

    @httpretty.activate
    def test_bsa(self):
        test_url = bart.service_advisory()
        httpretty.register_uri(httpretty.GET,
                               test_url,
                               body=bsa.text,
                               content_type='application/xml')
        advisories = client.bart.service_advisory()
        self.assertNotEqual(len(advisories[0].descriptions), 0)
        self.assertTrue(isinstance(advisories[0].expires, datetime))

    @httpretty.activate
    def test_train_count(self):
        test_url = bart.train_count()
        httpretty.register_uri(httpretty.GET,
                               test_url,
                               body=train_count.text,
                               content_type='application/xml')
        count = client.bart.train_count()
        self.assertTrue(isinstance(count, int))

    @httpretty.activate
    def test_elevator_status(self):
        test_url = bart.elevator_status()
        httpretty.register_uri(httpretty.GET,
                               test_url,
                               body=elevator.text,
                               content_type='application/xml')
        status = client.bart.elevator_status()
        self.assertTrue(len(status.descriptions) > 0)
