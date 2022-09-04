# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.common.util import configreader
from test.base import BaseTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class ConfigreaderTestCase(BaseTestCase):

    def test_read_app_config(self):
        conf = configreader.read('app')
        assert_that(conf, instance_of(object))
        assert_that(conf.config, has_key('daemon'))
        assert_that(conf.config, has_key('credentials'))

    def test_read_raise_error_if_not_exists(self):
        assert_that(calling(configreader.read).with_args('foo'), raises(Exception))
