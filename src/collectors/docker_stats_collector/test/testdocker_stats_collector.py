#!/usr/bin/python
# coding=utf-8
##########################################################################
import os
import json
from test import CollectorTestCase
from test import get_collector_config
from test import unittest
from test import run_only

try:
    from docker import Client
except ImportError:
    Client = None

from diamond.collector import Collector
from docker_stats_collector import DockerStatsCollector

dirname = os.path.dirname(__file__)
fixtures_path = os.path.join(dirname, 'fixtures/')

def run_only_if_docker_client_is_available(func):
    try:
        from docker import Client
    except ImportError:
        Client = None
    pred = lambda: Client is not None
    return run_only(func, pred)

class TestDockerStatsCollector(CollectorTestCase):

    def setUp(self):
        config = get_collector_config('DockerCollector', {
            'interval': 10,
        })

        self.collector = DockerStatsCollector(config, None)

    def test_import(self):
        self.assertTrue(DockerStatsCollector)


    def test_docker_stats_method_exists(self):
        self.assertTrue("stats" in dir(Client))

    def test_docker_stats_output_parse(self):
        stat = json.loads(open(os.path.join(fixtures_path, "example.stat")).read())
        for path in self.collector.METRICS: 
            val = self.collector.get_value(path, stat)
            self.assertTrue(val is not None)

    def test_docker_stats_output_parse_fail(self):
        stat = json.loads(open(os.path.join(fixtures_path, "example_empty.stat")).read())
        for path in self.collector.METRICS: 
            val = self.collector.get_value(path, stat)
            self.assertTrue(val is None)

if __name__ == "__main__":
    unittest.main()