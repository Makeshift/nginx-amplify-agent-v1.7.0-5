# -*- coding: utf-8 -*-
import copy

from hamcrest import *

from amplify.agent.collectors.nginx.accesslog import NginxAccessLogsCollector
from amplify.agent.objects.nginx.filters import Filter
from test.base import NginxCollectorTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class LogsFiltersTestCase(NginxCollectorTestCase):

    lines = [
        '178.23.225.78 - - [18/Jun/2015:17:22:25 +0000] "GET /img/docker.png HTTP/1.1" 200 0 ' +
        '"http://ec2-54-78-3-178.eu-west-1.compute.amazonaws.com:4000/" ' +
        '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) ' +
        'Chrome/43.0.2357.124 Safari/537.36"',

        '178.23.225.78 - - [18/Jun/2015:17:22:25 +0000] "GET /img/docker.png HTTP/1.2" 304 0 ' +
        '"http://ec2-54-78-3-178.eu-west-1.compute.amazonaws.com:4000/" ' +
        '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) ' +
        'Chrome/43.0.2357.124 Safari/537.36"',

        '178.23.225.78 - - [18/Jun/2015:17:22:25 +0000] "POST /img/super/docker.png HTTP/1.2" 304 2 ' +
        '"http://ec2-54-78-3-178.eu-west-1.compute.amazonaws.com:5000/" ' +
        '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) ' +
        'Chrome/43.0.2357.124 Safari/537.36"',

        '178.23.225.78 - - [18/Jun/2015:17:22:25 +0000] "GET /api/inventory/objects/ HTTP/1.1" 200 1093 ' +
        '"http://ec2-54-78-3-178.eu-west-1.compute.amazonaws.com:4000/" ' +
        '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) ' +
        'Chrome/43.0.2357.124 Safari/537.36"',

        '127.0.0.1 - - [18/Jun/2015:17:22:33 +0000] "POST /1.0/589fjinijenfirjf/meta/ HTTP/1.1" ' +
        '202 2 "-" "python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic"',

        '52.6.158.18 - - [18/Jun/2015:17:22:40 +0000] "GET /#/objects HTTP/2.1" 416 84 ' +
        '"-" "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)"',

        '52.6.158.18 - - [18/Jun/2015:17:23:40 +0000] "GET /#/objects HTTP/2.1" 502 84 ' +
        '"-" "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)"'
    ]

    def setup_method(self, method):
        super(LogsFiltersTestCase, self).setup_method(method)
        self.original_fake_object = copy.copy(self.fake_object)

    def teardown_method(self, method):
        self.fake_object = self.original_fake_object
        super(LogsFiltersTestCase, self).teardown_method(method)

    def test_simple_filter(self):
        self.fake_object.filters = [
            Filter(
                filter_rule_id=1,
                metric='nginx.http.status.2xx',
                data=[
                    ['$request_method', '~', 'GET'],
                    ['$status', '~', '200']
                ]
            ),
            Filter(
                filter_rule_id=2,
                metric='nginx.http.request.body_bytes_sent',
                data=[
                    ['$request_uri', '~', '/img*'],
                    ['$server_protocol', '~', 'HTTP/1.2']
                ]
            )
        ]

        collector = NginxAccessLogsCollector(object=self.fake_object, tail=self.lines)
        collector.collect()

        # check
        metrics = self.fake_object.statsd.flush()['metrics']
        assert_that(metrics, has_item('counter'))

        # counters
        counter = metrics['counter']
        for key in ('C|nginx.http.method.get', 'C|nginx.http.request.body_bytes_sent', 'C|nginx.http.status.3xx',
                    'C|nginx.http.status.2xx', 'C|nginx.http.method.post', 'C|nginx.http.v1_1',
                    'C|nginx.http.status.4xx', 'C|nginx.http.status.2xx||1', 'C|nginx.http.method.post'):
            assert_that(counter, has_key(key))

        # values
        assert_that(counter['C|nginx.http.method.get'][0][1], equal_to(5))
        assert_that(counter['C|nginx.http.method.post'][0][1], equal_to(2))
        assert_that(counter['C|nginx.http.status.2xx'][0][1], equal_to(3))

        # filter values
        assert_that(counter['C|nginx.http.status.2xx||1'][0][1], equal_to(2))

    def test_filter_with_negated(self):
        self.fake_object.filters = [
            Filter(filter_rule_id=1, metric='nginx.http.method.get', data=[['$status', '~', '200']]),
            Filter(filter_rule_id=2, metric='nginx.http.method.get', data=[['$status', '!~', '200']]),
            Filter(filter_rule_id=3, metric='nginx.http.method.get', data=[['$status', '~', '304']]),
            Filter(filter_rule_id=4, metric='nginx.http.method.get', data=[['$status', '!~', '304']]),
        ]

        collector = NginxAccessLogsCollector(object=self.fake_object, tail=self.lines)
        collector.collect()

        # check
        metrics = self.fake_object.statsd.flush()['metrics']
        assert_that(metrics, has_item('counter'))

        # counters
        counter = metrics['counter']
        assert_that(counter, has_key('C|nginx.http.method.get'))
        assert_that(counter['C|nginx.http.method.get'], contains(contains(is_(int), 5)))

        # filter values
        assert_that(counter, has_key('C|nginx.http.method.get||1'))
        assert_that(counter, has_key('C|nginx.http.method.get||2'))
        assert_that(counter, has_key('C|nginx.http.method.get||3'))
        assert_that(counter, has_key('C|nginx.http.method.get||4'))
        assert_that(counter['C|nginx.http.method.get||1'], contains(contains(is_(int), 2)))
        assert_that(counter['C|nginx.http.method.get||2'], contains(contains(is_(int), 3)))
        assert_that(counter['C|nginx.http.method.get||3'], contains(contains(is_(int), 1)))
        assert_that(counter['C|nginx.http.method.get||4'], contains(contains(is_(int), 4)))

    def test_unused_filter_defaults_zero(self):
        self.fake_object.filters = [
            Filter(filter_rule_id=1, metric='nginx.http.status.4xx', data=[['status', '~', '416']]),
            Filter(filter_rule_id=2, metric='nginx.http.status.4xx', data=[['status', '~', '300']]),
            Filter(filter_rule_id=3, metric='nginx.http.method.get', data=[['$request_uri', '~', '/img.*']]),
            Filter(filter_rule_id=4, metric='nginx.http.method.get', data=[['$request_uri', '~', 'abcdef']]),
        ]

        collector = NginxAccessLogsCollector(object=self.fake_object, tail=self.lines)
        collector.collect()

        # check
        metrics = self.fake_object.statsd.flush()['metrics']
        assert_that(metrics, has_item('counter'))

        # counters
        counter = metrics['counter']

        # filter values
        assert_that(counter, has_key('C|nginx.http.status.4xx||1'))
        assert_that(counter, has_key('C|nginx.http.status.4xx||2'))
        assert_that(counter, has_key('C|nginx.http.method.get||3'))
        assert_that(counter, has_key('C|nginx.http.method.get||4'))
        assert_that(counter['C|nginx.http.status.4xx||1'], contains(contains(is_(int), 1)))
        assert_that(counter['C|nginx.http.status.4xx||2'], contains(contains(is_(int), 0)))
        assert_that(counter['C|nginx.http.method.get||3'], contains(contains(is_(int), 2)))
        assert_that(counter['C|nginx.http.method.get||4'], contains(contains(is_(int), 0)))

    def test_regex_filter(self):
        self.fake_object.filters = [
            Filter(
                filter_rule_id=2,
                metric='nginx.http.request.body_bytes_sent',
                data=[
                    ['$request_uri', '~', '/img.*'],
                    ['$server_protocol', '~', 'HTTP/1.2']
                ]
            )
        ]

        collector = NginxAccessLogsCollector(object=self.fake_object, tail=self.lines)
        collector.collect()

        # check
        metrics = self.fake_object.statsd.flush()['metrics']
        assert_that(metrics, has_item('counter'))

        # counters
        counter = metrics['counter']
        for key in ('C|nginx.http.method.get', 'C|nginx.http.request.body_bytes_sent', 'C|nginx.http.status.3xx',
                    'C|nginx.http.status.2xx', 'C|nginx.http.method.post', 'C|nginx.http.v1_1',
                    'C|nginx.http.status.4xx', 'C|nginx.http.request.body_bytes_sent||2', 'C|nginx.http.method.post'):
            assert_that(counter, has_key(key))

        # values
        assert_that(counter['C|nginx.http.method.get'][0][1], equal_to(5))
        assert_that(counter['C|nginx.http.method.post'][0][1], equal_to(2))
        assert_that(counter['C|nginx.http.status.2xx'][0][1], equal_to(3))

        # filter values
        assert_that(counter['C|nginx.http.request.body_bytes_sent||2'][0][1], equal_to(2))

    def test_server_name(self):
        self.fake_object.filters = [
            Filter(
                filter_rule_id=2,
                metric='nginx.http.status.2xx',
                data=[
                    ['$server_name', '~', 'differentsimgirls.com']
                ]
            )
        ]

        collector = NginxAccessLogsCollector(
            object=self.fake_object,
            log_format='$remote_addr - $remote_user [$time_local] \"$request\" $status $body_bytes_sent ' +
                       '\"$http_referer\" \"$http_user_agent\" \"$http_x_forwarded_for\" ' +
                       'rt=$request_time ua=\"$upstream_addr\" us=\"$upstream_status\" ' +
                       'ut=\"$upstream_response_time\" ul=\"$upstream_response_length\" ' +
                       'cs=$upstream_cache_status sn=$server_name',
            tail=[
                '104.236.93.23 - - [05/May/2016:12:52:50 +0200] "GET / HTTP/1.1" 200 28275 "-" ' +
                '"curl/7.35.0" "-" rt=0.082 ua="-" us="-" ut="-" ul="-" cs=- sn=differentsimgirls.com'
            ]
        )
        collector.collect()

        # check
        metrics = self.fake_object.statsd.flush()['metrics']
        assert_that(metrics, has_item('counter'))
        counter = metrics['counter']

        # check our metric
        assert_that(counter['C|nginx.http.status.2xx'][0][1], equal_to(1))
        assert_that(counter['C|nginx.http.status.2xx||2'][0][1], equal_to(1))

    def test_timers_with_filters(self):
        self.fake_object.filters = [
            Filter(
                filter_rule_id=3,
                metric='nginx.upstream.response.time.median',
                data=[
                    ['$status', '~', '200']
                ]
            ),
            Filter(
                filter_rule_id=4,
                metric='nginx.upstream.response.time.max',
                data=[
                    ['$status', '~', '400']
                ]
            )
        ]

        collector = NginxAccessLogsCollector(
            object=self.fake_object,
            log_format='$remote_addr - $remote_user [$time_local] \"$request\" $status $body_bytes_sent ' +
                       '\"$http_referer\" \"$http_user_agent\" \"$http_x_forwarded_for\" ' +
                       'rt=$request_time ua=\"$upstream_addr\" us=\"$upstream_status\" ' +
                       'ut=\"$upstream_response_time\" ul=\"$upstream_response_length\" ' +
                       'cs=$upstream_cache_status sn=$server_name',
            tail=[
                '104.236.93.23 - - [05/May/2016:12:52:50 +0200] "GET / HTTP/1.1" 200 28275 "-" ' +
                '"curl/7.35.0" "-" rt=0.082 ua="-" us="-" ut="1.000" ul="-" cs=- sn=differentsimgirls.com',
                '104.236.93.23 - - [05/May/2016:12:52:50 +0200] "GET / HTTP/1.1" 200 28275 "-" ' +
                '"curl/7.35.0" "-" rt=0.082 ua="-" us="-" ut="3.000" ul="-" cs=- sn=differentsimgirls.com',
                '104.236.93.23 - - [05/May/2016:12:52:50 +0200] "GET / HTTP/1.1" 200 28275 "-" ' +
                '"curl/7.35.0" "-" rt=0.082 ua="-" us="-" ut="5.000" ul="-" cs=- sn=differentsimgirls.com',
                '104.236.93.23 - - [05/May/2016:12:52:50 +0200] "GET / HTTP/1.1" 400 28275 "-" ' +
                '"curl/7.35.0" "-" rt=0.082 ua="-" us="-" ut="7.000" ul="-" cs=- sn=differentsimgirls.com'
            ]
        )
        collector.collect()

        metrics = self.fake_object.statsd.flush()['metrics']
        timer = metrics['timer']
        for key in ['G|nginx.upstream.response.time.max', 'G|nginx.upstream.response.time.median',
                    'G|nginx.upstream.response.time.pctl95', 'C|nginx.upstream.response.time.count',
                    'G|nginx.upstream.response.time.max||3', 'G|nginx.upstream.response.time.median||3',
                    'G|nginx.upstream.response.time.pctl95||3', 'C|nginx.upstream.response.time.count||3',
                    'G|nginx.upstream.response.time.max||4', 'G|nginx.upstream.response.time.median||4',
                    'G|nginx.upstream.response.time.pctl95||4', 'C|nginx.upstream.response.time.count||4']:
            assert_that(timer, has_key(key))

        assert_that(timer["G|nginx.upstream.response.time.max||3"][0][1], equal_to(5.000))
        assert_that(timer["G|nginx.upstream.response.time.median||3"][0][1], equal_to(3.000))
        assert_that(timer["C|nginx.upstream.response.time.count||3"][0][1], equal_to(3))
        assert_that(timer["G|nginx.upstream.response.time.max||4"][0][1], equal_to(7.000))
        assert_that(timer["G|nginx.upstream.response.time.median||4"][0][1], equal_to(7.000))
        assert_that(timer["C|nginx.upstream.response.time.count||4"][0][1], equal_to(1))
        assert_that(timer["G|nginx.upstream.response.time.max"][0][1], equal_to(7.000))
        assert_that(timer["G|nginx.upstream.response.time.median"][0][1], equal_to(4.000))
        assert_that(timer["C|nginx.upstream.response.time.count"][0][1], equal_to(4))

    def test_separate_4xx_5xx_with_filters(self):
        self.fake_object.filters = [
            Filter(
                filter_rule_id=1,
                metric='nginx.http.status.502',
                data=[
                    ['$request_method', '~', 'GET'],
                ]
            )
        ]

        collector = NginxAccessLogsCollector(object=self.fake_object, tail=self.lines)
        collector.collect()

        # check
        metrics = self.fake_object.statsd.flush()['metrics']
        assert_that(metrics, has_item('counter'))

        # counters
        counter = metrics['counter']
        for key in ('C|nginx.http.method.get', 'C|nginx.http.request.body_bytes_sent', 'C|nginx.http.status.3xx',
                    'C|nginx.http.status.2xx', 'C|nginx.http.method.post', 'C|nginx.http.v1_1',
                    'C|nginx.http.status.4xx', 'C|nginx.http.status.5xx', 'C|nginx.http.status.502||1',
                    'C|nginx.http.method.post'):
            assert_that(counter, has_key(key))

        # values
        assert_that(counter['C|nginx.http.method.get'][0][1], equal_to(5))
        assert_that(counter['C|nginx.http.method.post'][0][1], equal_to(2))
        assert_that(counter['C|nginx.http.status.5xx'][0][1], equal_to(1))

        # filter values
        assert_that(counter['C|nginx.http.status.502||1'][0][1], equal_to(1))
