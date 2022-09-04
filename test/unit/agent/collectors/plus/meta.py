# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.collectors.plus.meta import PlusObjectMetaCollector
from amplify.agent.common.context import context
from amplify.agent.objects.plus.object import PlusObject
from test.fixtures.defaults import DEFAULT_UUID
from test.base import BaseTestCase

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusObjectMetaCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(PlusObjectMetaCollectorTestCase, self).setup_method(method)
        self.plus_obj = PlusObject(local_name='test_obj', parent_local_id='nginx123', root_uuid=DEFAULT_UUID)

    def teardown_method(self, method):
        self.plus_obj = None
        super(PlusObjectMetaCollectorTestCase, self).teardown_method(method)

    def test_meta_collect(self):
        meta_collector = PlusObjectMetaCollector(object=self.plus_obj)
        meta_collector.collect()

        meta = self.plus_obj.metad.current
        assert_that(meta, equal_to(
            {
                'type': 'nginx_plus',
                'local_name': 'test_obj',
                'local_id': 'a9b8f9caa98ee30806a4a7c17ba393330059317600d768e4c81b2d585f7b9a6a',
                'root_uuid': DEFAULT_UUID,
                'hostname': context.hostname,
                'version': None  # Version will fail because this test is done in a vacuum without parent nginx
            }
        ))
