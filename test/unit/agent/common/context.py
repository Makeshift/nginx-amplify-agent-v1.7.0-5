# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.common.context import context
from test.base import BaseTestCase
from test.fixtures.defaults import *

__author__ = "Arie van Luttikhuizen"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Arie van Luttikhuizen"
__email__ = "arie@nginx.com"


class ContextTestCase(BaseTestCase):
    def test_freeze_api_url(self):
        # check that if api_url is not set it will not prevent agent from setting api_url from cloud
        context.app_config['cloud']['api_url'] = ''
        context.setup(app='test', app_config=context.app_config.default)
        assert_that(context.freeze_api_url, equal_to(False))

        # check that an api_url from our receiver's domain will not prevent agent from setting api_url from cloud
        context.app_config['cloud']['api_url'] = 'https://receiver.amplify.nginx.com:443/1.1'
        context.setup(app='test', app_config=context.app_config.default)
        assert_that(context.freeze_api_url, equal_to(False))

        # check that a custom api_url will prevent agent from setting api_url from cloud
        context.app_config['cloud']['api_url'] = 'http://some.other.domain/endpoint/'
        context.setup(app='test', app_config=context.app_config.default)
        assert_that(context.freeze_api_url, equal_to(True))

    def test_uuid(self):
        assert_that(context.app_config['credentials'], has_entry('imagename', ''))
        assert_that(context.app_config['credentials'], has_entry('hostname', DEFAULT_HOST))
        assert_that(context.app_config['credentials'], has_entry('api_key', DEFAULT_API_KEY))
        assert_that(context.app_config['credentials'], has_entry('uuid', DEFAULT_UUID))
        assert_that(context.uuid, equal_to(DEFAULT_UUID))


class ContextContainerTestCase(BaseTestCase):

    def setup_method(self, method):
        super(ContextContainerTestCase, self).setup_method(method)
        context.app_config['credentials']['imagename'] = 'DockerTest'
        context.setup(app='test', app_config=context.app_config.default)

    def teardown_method(self, method):
        context.app_config['credentials']['imagename'] = None
        context.app_config['credentials']['uuid'] = DEFAULT_UUID
        context.setup(app='test', app_config=context.app_config.default)

    def test_uuid(self):
        assert_that(context.app_config['credentials'], has_entry('imagename', 'DockerTest'))
        assert_that(context.app_config['credentials'], has_entry('api_key', DEFAULT_API_KEY))
        assert_that(context.app_config['credentials'], has_entry('uuid', 'container-DockerTest'))
        assert_that(context.uuid, equal_to('container-DockerTest'))
