# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.objects.nginx.log.access import NginxAccessLogParser
from test.base import BaseTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class LogParserTestCase(BaseTestCase):

    def test_prepare_combined(self):
        """
        Check that we can prepare standart format:
        '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"'
        """
        parser = NginxAccessLogParser()

        expected_keys = ['remote_addr', 'remote_user', 'time_local',
                         'request', 'status', 'body_bytes_sent',
                         'http_referer', 'http_user_agent']

        for key in expected_keys:
            assert_that(parser.keys, has_item(key))

    def test_parse_combined(self):
        """
        Checks that we can parse standart format

        log example:
        127.0.0.1 - - [02/Jul/2015:14:49:48 +0000] "GET /basic_status HTTP/1.1" 200 110 "-" "python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic"
        """
        parser = NginxAccessLogParser()

        line = '127.0.0.1 - - [02/Jul/2015:14:49:48 +0000] "GET /basic_status HTTP/1.1" 200 110 "-" "python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic"'
        parsed = parser.parse(line)

        # basic keys
        common_expected_keys = ['remote_addr', 'remote_user', 'time_local',
                                'request', 'status', 'body_bytes_sent',
                                'http_referer', 'http_user_agent']

        for key in common_expected_keys:
            assert_that(parsed, has_item(key))

        assert_that(parsed['status'], equal_to('200'))
        assert_that(parsed['body_bytes_sent'], equal_to(110))
        assert_that(parsed['remote_user'], equal_to('-'))
        assert_that(parsed['http_user_agent'], equal_to('python-requests/2.2.1 CPython/2.7.6 Linux/3.13.0-48-generic'))

        # request keys
        request_expected_keys = NginxAccessLogParser.request_variables
        for key in request_expected_keys:
            assert_that(parsed, has_item(key))

        assert_that(parsed['request_method'], equal_to('GET'))
        assert_that(parsed['request_uri'], equal_to('/basic_status'))
        assert_that(parsed['server_protocol'], equal_to('HTTP/1.1'))

    def test_malformed_request(self):
        line = '10.0.0.1 - - [03/Jul/2015:04:46:18 -0400] "/xxx?q=1 GET" 400 173 "-" "-" "-"'

        parser = NginxAccessLogParser()
        parsed = parser.parse(line)

        assert_that(parsed['malformed'], equal_to(True))
        assert_that(parsed['status'], equal_to('400'))

    def test_simple_user_format(self):
        """
        Check some user format
        """
        user_format = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" "$host" "$request_time" $gzip_ratio'

        expected_keys = ['remote_addr', 'remote_user', 'time_local', 'request_time',
                         'request', 'status', 'body_bytes_sent',
                         'http_x_forwarded_for', 'http_referer', 'http_user_agent', 'host', 'gzip_ratio']

        parser = NginxAccessLogParser(user_format)

        for key in expected_keys:
            assert_that(parser.keys, has_item(key))

        lines = [
            '141.101.234.201 - - [03/Jul/2015:10:52:33 +0300] "POST /wp-login.php HTTP/1.1" 200 3809 "http://estevmeste.ru/wp-login.php" "Mozilla/5.0 (Windows NT 6.0; rv:34.0) Gecko/20100101 Firefox/34.0" "-" "estevmeste.ru" "0.001" -',
            '95.211.80.227 - - [03/Jul/2015:10:52:57 +0300] "PUT /stub_status HTTP/1.1" 200 109 "-" "cloudwatch-nginx-agent/1.0" "-" "defan.pp.ru" "0.001" -',
            '95.211.80.227 - - [03/Jul/2015:10:54:00 +0300] "GET /stub_status HTTP/2.1" 200 109 "-" "cloudwatch-nginx-agent/1.0" "-" "defan.pp.ru" "0.134" -'
        ]

        for line in lines:
            parsed = parser.parse(line)
            for key in expected_keys:
                assert_that(parsed, has_item(key))
            assert_that(parsed['host'], is_in(['defan.pp.ru', 'estevmeste.ru']))
            assert_that(parsed['gzip_ratio'], equal_to(0))
            assert_that(parsed['malformed'], equal_to(False))
            assert_that(parsed['request_time'], is_(instance_of(list)))
            assert_that(parsed['request_time'][0], is_(instance_of(float)))

        # check first line
        parsed = parser.parse(lines[0])
        assert_that(parsed['request_uri'], equal_to('/wp-login.php'))

        # check second line
        parsed = parser.parse(lines[1])
        assert_that(parsed['request_method'], equal_to('PUT'))

        # check second line
        parsed = parser.parse(lines[2])
        assert_that(parsed['server_protocol'], equal_to('HTTP/2.1'))
        assert_that(parsed['request_time'], equal_to([0.134]))

    def test_complex_user_format(self):
        """
        Check some super complex user format with cache
        """
        user_format = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" "$upstream_addr" "$upstream_cache_status" $connection/$connection_requests'
        line = '217.15.195.202 - - [03/Jul/2015:11:12:53 +0300] "GET /gsat/9854/5231/14 HTTP/1.1" 200 11901 "-" "tile-fetcher/0.1" "-" "173.194.32.133:80" "MISS" 62277/22'

        expected_keys = [
            'remote_addr', 'remote_user', 'time_local', 'connection',
            'request', 'status', 'body_bytes_sent', 'http_x_forwarded_for',
            'http_referer', 'http_user_agent', 'upstream_addr', 'upstream_cache_status', 'connection_requests'
        ]
        parser = NginxAccessLogParser(user_format)
        for key in expected_keys:
            assert_that(parser.keys, has_item(key))

        parsed = parser.parse(line)
        for key in expected_keys:
            assert_that(parsed, has_item(key))

        assert_that(parsed['upstream_addr'], equal_to(['173.194.32.133:80']))
        assert_that(parsed['connection'], equal_to('62277'))
        assert_that(parsed['malformed'], equal_to(False))
        assert_that(parsed['upstream_cache_status'], equal_to('MISS'))

    def test_malformed_request_time(self):
        user_format = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" "$host" "$request_time" $gzip_ratio'
        line = '141.101.234.201 - - [03/Jul/2015:10:52:33 +0300] "POST /wp-login.php HTTP/1.1" 200 3809 "http://estevmeste.ru/wp-login.php" "Mozilla/5.0 (Windows NT 6.0; rv:34.0) Gecko/20100101 Firefox/34.0" "-" "estevmeste.ru" "1299760000.321" -'

        parser = NginxAccessLogParser(user_format)
        parsed = parser.parse(line)

        assert_that(parsed, is_not(has_item('request_time')))

    def test_our_config(self):
        user_format = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" rt="$request_time" ua="$upstream_addr" us="$upstream_status" ut="$upstream_response_time" "$gzip_ratio"'
        line = '127.0.0.1 - - [03/Jul/2015:14:09:38 +0000] "GET /basic_status HTTP/1.1" 200 100 "-" "curl/7.35.0" "-" rt="0.000" ua="-" us="-" ut="-" "-"'

        parser = NginxAccessLogParser(user_format)
        parsed = parser.parse(line)

        assert_that(parsed, has_item('request_time'))

    def test_lonerr_config(self):
        user_format = '$remote_addr - $remote_user [$time_local] ' + \
                      '"$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" ' + \
                      'rt=$request_time ut="$upstream_response_time" cs=$upstream_cache_status'

        line = \
            '1.2.3.4 - - [22/Jan/2010:19:34:21 +0300] "GET /foo/ HTTP/1.1" 200 11078 ' + \
            '"http://www.rambler.ru/" "Mozilla/5.0 (Windows; U; Windows NT 5.1" rt=0.010 ut="2.001, 0.345" cs=MISS'

        parser = NginxAccessLogParser(user_format)
        parsed = parser.parse(line)

        assert_that(parsed, has_item('upstream_response_time'))

    def test_soukiii_config(self):
        """
        This test is modelled after user soukiii who reported an error in parsing.
        https://github.com/nginxinc/nginx-amplify-agent/issues/7
        """
        user_format = '$remote_addr - [$time_local] $request_method $scheme "$request_uri"  ' + \
                      '$status $request_time $body_bytes_sent  "$http_referer" ' + \
                      '"$http_user_agent" $host'

        line = \
            '85.25.210.234 - [17/Nov/2015:00:20:50 +0100] GET https "/robots.txt"  200 0.024 240  "-" ' + \
            '"Mozilla/5.0 (compatible; worldwebheritage.org/1.1; +crawl@worldwebheritage.org)" www.nakupni-dum-praha.cz'

        parser = NginxAccessLogParser(user_format)
        parsed = parser.parse(line)

        assert_that(parsed, has_item('status'))
        assert_that(parsed, has_item('request_method'))

    def test_recommended_config(self):
        """
        This test is modelled after our 'recommended' configuration format recently added to our docs.

        https://github.com/nginxinc/nginx-amplify-doc/blob/master/amplify-guide.md#additional-http-metrics
        """
        user_format = \
            '$remote_addr - $remote_user [$time_local] "$request" ' + \
            ' $status $body_bytes_sent "$http_referer" ' + \
            '"$http_user_agent" "$http_x_forwarded_for" ' + \
            'rt=$request_time ua="$upstream_addr" ' + \
            'us="$upstream_status" ut="$upstream_response_time" ' + \
            'cs=$upstream_cache_status'

        expected_keys = [
            'remote_addr', 'remote_user', 'time_local', 'request_method', 'request_uri', 'server_protocol', 'status',
            'body_bytes_sent', 'http_referer', 'http_user_agent', 'http_x_forwarded_for', 'request_time',
            'upstream_addr', 'upstream_status', 'upstream_response_time', 'upstream_cache_status'
        ]

        # first try to parse simple line
        simple_line = \
            '85.25.210.234 - - [22/Jan/2010:19:34:21 +0300] "GET /foo/ HTTP/1.1" ' + \
            ' 200 11078 "http://www.rambler.ru/" ' + \
            '"Mozilla/5.0 (Windows; U; Windows NT 5.1" "-" ' + \
            'rt=0.024 ua="-" ' + \
            'us="-" ut="0.024" ' + \
            'cs="-"'

        parser = NginxAccessLogParser(user_format)
        parsed = parser.parse(simple_line)

        for key in expected_keys:
            assert_that(parsed, has_item(key))

        # now try to parse request with /
        simple_line = \
            '85.25.210.234 - - [22/Jan/2010:19:34:21 +0300] "GET / HTTP/2.0" ' + \
            ' 200 11078 "http://www.rambler.ru/" ' + \
            '"Mozilla/5.0 (Windows; U; Windows NT 5.1" "-" ' + \
            'rt=0.024 ua="-" ' + \
            'us="-" ut="0.024" ' + \
            'cs="-"'

        parser = NginxAccessLogParser(user_format)
        parsed = parser.parse(simple_line)

        for key in expected_keys:
            assert_that(parsed, has_item(key))

        assert_that(parsed, has_item('request_uri'))
        assert_that(parsed['request_uri'], equal_to('/'))
        assert_that(parsed['server_protocol'], equal_to('HTTP/2.0'))

    def test_tab_config(self):
        user_format = \
            '"$time_local"\t"$remote_addr"\t"$http_host"\t"$request"\t"$status"\t"$body_bytes_sent\t' + \
            '"$http_referer"\t"$http_user_agent"\t"$http_x_forwarded_for"'

        expected_keys = [
            'time_local', 'remote_addr', 'http_host', 'request_method', 'request_uri', 'server_protocol', 'status',
            'body_bytes_sent', 'http_referer', 'http_user_agent', 'http_x_forwarded_for'
        ]

        simple_line = \
            '"27/Jan/2016:12:30:04 -0800"	"173.186.135.227"	"leete.ru"	' + \
            '"GET /img/_data/combined/j6vnc0.css HTTP/2.0"	"200"	"5909	"https://leete.ru/img/"' + \
            '	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) ' + \
            'Chrome/47.0.2526.111 Safari/537.36"	"-"'

        parser = NginxAccessLogParser(user_format)
        parsed = parser.parse(simple_line)

        for key in expected_keys:
            assert_that(parsed, has_item(key))

    def test_json_config(self):
        user_format = \
            '{"time_local": "$time_local","browser": [{"modern_browser": "$modern_browser",' + \
            '"ancient_browser": "$ancient_browser","msie": "$msie"}],"core": [{"args": "$args","uri": "$uri"}]}'

        expected_keys = [
            'time_local', 'modern_browser', 'ancient_browser', 'msie', 'args', 'uri'
        ]

        simple_line = \
            '{"time_local": "27/Jan/2016:12:30:04 -0800","browser": [{"modern_browser": "-","ancient_browser": "1","msie": "-"}],"core": [{"args": "-","uri": "/status"}]}'

        parser = NginxAccessLogParser(user_format)
        parsed = parser.parse(simple_line)

        for key in expected_keys:
            assert_that(parsed, has_item(key))

    def test_format_with_trailing_space(self):
        user_format = '$remote_addr - $remote_user [$time_local] "$request" ' + \
                      '$status $body_bytes_sent "$http_referer" ' + \
                      '"$http_user_agent" "$http_x_forwarded_for" ' + \
                      'rt=$request_time ua="$upstream_addr" ' + \
                      'us="$upstream_status" ut="$upstream_response_time" ' + \
                      'ul="$upstream_response_length" ' + \
                      'cs=$upstream_cache_status ' + \
                      'sn=$server_name     '

        expected_keys = [
            'time_local', 'status'
        ]

        line = '180.76.15.138 - - [05/May/2016:15:26:57 +0200] "GET / HTTP/1.1" 200 16060 ' + \
               '"-" "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)" ' + \
               '"-" rt=0.258 ua="-" us="-" ut="-" ul="-" cs=- sn=differentsimgirls.com     '

        parser = NginxAccessLogParser(user_format)
        parsed = parser.parse(line)

        for key in expected_keys:
            assert_that(parsed, has_item(key))

    def test_comma_separated_values(self):
        """
        Check some super complex user format with cache
        """
        user_format = '"$upstream_addr" $upstream_status'
        line = '"173.194.32.133:80, 173.194.32.133:81, 173.194.32.133:82" 200, 200, 200'

        expected_keys = [
            'upstream_addr', 'upstream_status'
        ]
        parser = NginxAccessLogParser(user_format)
        for key in expected_keys:
            assert_that(parser.keys, has_item(key))

        parsed = parser.parse(line)
        for key in expected_keys:
            assert_that(parsed, has_item(key))

        assert_that(parsed['upstream_addr'], equal_to(['173.194.32.133:80', '173.194.32.133:81', '173.194.32.133:82']))
        assert_that(parsed['upstream_status'], equal_to(['200', '200', '200']))

    def test_format_with_braces(self):
        """
        Check log format with braces
        """
        user_format = '$remote_addr - $remote_user [$time_local] $request ' \
                      '"$status" $body_bytes_sent "$http_referer" ' \
                      '"$http_user_agent" "$http_x_forwarded_for" ' \
                      '"http-host=$host" "elapsed=${request_time}s" ' \
                      '"scheme=${scheme}"'

        expected_keys = [
            'remote_user', 'remote_addr', 'time_local', 'status',
            'request_time', 'scheme', 'host',
        ]

        parser = NginxAccessLogParser(user_format)
        for key in expected_keys:
            assert_that(parser.keys, has_item(key))

    def test_malformed_request_doesnt_raise_exception(self):
        log_format = '$remote_addr - $remote_user [$time_local] "$request" ' + \
                     '$status $body_bytes_sent "$http_referer" ' + \
                     '"$http_user_agent" "$http_x_forwarded_for" "$server_name" $request_id ' + \
                     '$upstream_http_x_amplify_upstream ' + \
                     '"$upstream_addr" "$upstream_response_time" "$upstream_status" ' + \
                     '$ssl_protocol $ssl_cipher $connection/$connection_requests $request_length "$request_time"'

        parser = NginxAccessLogParser(log_format)
        line = '139.162.124.167 - - [16/Mar/2017:00:53:14 +0000] "\x04\x01\x1F\x00\x00\x00\x00\x00\x00" ' + \
               '400 166 "-" "-" "-" "receiver.amplify.nginx.com" 9dbaa8264268b8aa55fb9af077834702 ' + \
               '- "-" "-" "-" - - 42433164/1 0 "0.108"'

        parsed = parser.parse(line)

        # this block is true for GSH new parser...comment for now.
        # for key in parser.keys:
        #     # new parser will get this value, but post parsing logic ignores
        #     # empty values for '*_time' variables.
        #     if not key.endswith('_time'):
        #         assert_that(parsed, has_item(key))

        assert_that(parsed['malformed'], equal_to(True))

    def test_empty_server_name(self):
        # log_format and lines for this test were taken from AMPDEV-1110

        log_format = (
            '$remote_addr - $remote_user [$time_local] "$request" '
            '$status $body_bytes_sent "$http_referer" '
            '"$http_user_agent" "$http_x_forwarded_for" '
            '"$host" sn="$server_name" '
            'rt=$request_time '
            'ua="$upstream_addr" us="$upstream_status" '
            'ut="$upstream_response_time" ul="$upstream_response_length" '
            'cs=$upstream_cache_status'
        )

        parser = NginxAccessLogParser(log_format)

        assert_that(parser.keys, contains(
            'remote_addr', 'remote_user', 'time_local', 'request',
            'status', 'body_bytes_sent', 'http_referer',
            'http_user_agent', 'http_x_forwarded_for',
            'host', 'server_name',
            'request_time',
            'upstream_addr', 'upstream_status',
            'upstream_response_time', 'upstream_response_length',
            'upstream_cache_status'
        ))

        lines = [
            '192.168.128.23 - - [13/Jul/2017:20:04:15 +0000] "GET /api/1/nats/worker_connections HTTP/1.1" 200 522 "-" "Python-urllib/3.5" "-" "sticky-1.gnt.nginx.com" sn="" rt=0.000 ua="-" us="-" ut="-" ul="-" cs=-',
            '192.168.128.23 - - [13/Jul/2017:20:04:15 +0000] "GET /api/1/http/upstreams HTTP/1.1" 200 2396 "-" "Python-urllib/3.5" "-" "sticky-1.gnt.nginx.com" sn="" rt=0.000 ua="-" us="-" ut="-" ul="-" cs=-'
        ]

        for line in lines:
            parsed = parser.parse(line)
            assert_that(parsed, not_none())
            assert_that(parsed, has_entries(remote_addr='192.168.128.23', server_name=''))

    def test_ends_with_space_then_empty_var(self):
        log_format = (
            '$remote_addr | $http_x_real_ip | $status | $request | $upstream_addr | $upstream_status | $upstream_response_length | $body_bytes_sent | '
            '$upstream_header_time | $upstream_response_time | $upstream_cache_status | $host | $time_local | $http_x_forwarded_for | $http_referer | $http_user_agent | $request_time | '
            '$ssl_protocol | $ssl_cipher | $connection_requests | $connection | $bytes_sent | $server_port | $gzip_ratio | '
            '$time_iso8601 | $geoip_country_code | $geoip_city_country_name | $geoip_region | $geoip_city | '
            '$region | $city_geo | $city_mm | $tz_geo $tz_mm'
        )

        line = (
            '127.0.0.1 | 192.168.0.100 | 200 | GET /foo/bar/123/ HTTP/1.1 | 192.168.0.99:9000 | 200 | 599866 | 52736 | '
            '1.500 | 1.500 | - | www.example.com | 05/Jun/2018:10:46:46 +0300 | 192.168.0.100 | - | Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24 | 1.500 | '
            'TLSv1.2 | ECDHE-RSA-AES128-GCM-SHA256 | 96 | 12345678 | 54099 | 443 | 11.38 | '
            '2018-06-05T10:46:46+03:00 | RU | Russian Federation | - | - | '
            '77 | 0JzQvtGB0LrQstCw |  | UTC+3 '
        )

        parser = NginxAccessLogParser(log_format)
        parsed = parser.parse(line)

        assert_that(parsed['region'], equal_to('77'))
        assert_that(parsed['city_geo'], equal_to('0JzQvtGB0LrQstCw'))
        assert_that(parsed['city_mm'], equal_to(''))
        assert_that(parsed['tz_geo'], equal_to('UTC+3'))
        assert_that(parsed['tz_mm'], equal_to(''))

    def test_format_with_multiple_lines(self):

        splunk_log_format = '''timestamp=$time_iso8601
                          level=6
                          body_bytes_sent=$body_bytes_sent
                          correlation_id=$upstream_http_x_correlation_id
                          http_referrer="$http_referer"
                          http_user_agent="$http_user_agent"
                          level_name=info
                          organisation=Retail
                          path="$scheme://$server_name $uri"
                          querystring=$args
                          remote_addr="$remote_addr"
                          request_duration=$request_time
                          request_method=$request_method
                          request_path=$uri
                          request_uri=$request_uri
                          server_name=$server_name
                          server_protocol=$server_protocol
                          source_system="$upstream_http_x_source_system"
                          status=$status
                          upstream_addr="$upstream_addr"
                          upstream_cache_status=$upstream_cache_status
                          upstream_connect_time=$upstream_connect_time
                          upstream_header_time=$upstream_header_time
                          upstream_response_time=$upstream_response_time
                          upstream_status=$upstream_status
                          '''
        splunk_log_record = '''timestamp=2018-07-17T18:07:31+00:00
                          level=6
                          body_bytes_sent=97
                          correlation_id=-
                          http_referrer="-"
                          http_user_agent="nginx-amplify-agent/1.5.0-1"
                          level_name=info
                          organisation=Retail
                          path="http:// /basic_status"
                          querystring=-
                          remote_addr="127.0.0.1"
                          request_duration=0.000
                          request_method=GET
                          request_path=/basic_status
                          request_uri=/basic_status
                          server_name=
                          server_protocol=HTTP/1.1
                          source_system="-"
                          status=200
                          upstream_addr="-"
                          upstream_cache_status=-
                          upstream_connect_time=-
                          upstream_header_time=-
                          upstream_response_time=-
                          upstream_status=-
                          '''

        parser = NginxAccessLogParser(splunk_log_format)
        parsed = parser.parse(splunk_log_record)

        expected_keys = [
            "time_iso8601",
            "body_bytes_sent",
            "upstream_http_x_correlation_id",
            "http_referer",
            "http_user_agent",
            "scheme",
            "uri",
            "args",
            "remote_addr",
            "request_time",
            "request_method",
            "request_uri",
            "server_name",
            "server_protocol",
            "upstream_http_x_source_system",
            "status",
            "upstream_addr",
            "upstream_cache_status",
            "upstream_status"
        ]
        # check for the keys
        assert_that(parsed, has_items(*expected_keys))

        # check for values
        assert_that(parsed['body_bytes_sent'], equal_to(97))
        assert_that(parsed['time_iso8601'], equal_to('2018-07-17T18:07:31+00:00'))
        assert_that(parsed['http_user_agent'], equal_to('nginx-amplify-agent/1.5.0-1'))
