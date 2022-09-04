# -*- coding: utf-8 -*-
import os

from hamcrest import *

from test.base import WithConfigTestCase, disabled_test
from test.unit.agent.common.config.app import TestingConfig


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class AbstractConfigTestCase(WithConfigTestCase):

    @disabled_test  # disabled because it keeps altering our etc/agent.conf.testing file
    def test_change_var_and_save(self):
        """
        Test that configreader saves new config if it doesn't exist
        """
        self.mk_test_config()

        assert_that(os.path.exists(TestingConfig.filename), equal_to(True))
        conf = TestingConfig()
        conf.save('credentials', 'uuid', '123')
        assert_that(conf['credentials']['uuid'], equal_to('123'))

        for line in file(TestingConfig.filename).readlines():
            if 'uuid' in line:
                assert_that(line, contains_string('123'))
