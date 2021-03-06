# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import six
from tests.compat import mock

import pkg_resources

from airflow.www_rbac import app as application


class PluginsTestRBAC(unittest.TestCase):
    def setUp(self):
        self.app, self.appbuilder = application.create_app(testing=True)

    def test_flaskappbuilder_views(self):
        from tests.plugins.test_plugin import v_appbuilder_package
        appbuilder_class_name = str(v_appbuilder_package['view'].__class__.__name__)
        plugin_views = [view for view in self.appbuilder.baseviews
                        if view.blueprint.name == appbuilder_class_name]

        self.assertTrue(len(plugin_views) == 1)

        # view should have a menu item matching category of v_appbuilder_package
        links = [menu_item for menu_item in self.appbuilder.menu.menu
                 if menu_item.name == v_appbuilder_package['category']]

        self.assertTrue(len(links) == 1)

        # menu link should also have a link matching the name of the package.
        link = links[0]
        self.assertEqual(link.name, v_appbuilder_package['category'])
        self.assertEqual(link.childs[0].name, v_appbuilder_package['name'])

    def test_flaskappbuilder_menu_links(self):
        from tests.plugins.test_plugin import appbuilder_mitem

        # menu item should exist matching appbuilder_mitem
        links = [menu_item for menu_item in self.appbuilder.menu.menu
                 if menu_item.name == appbuilder_mitem['category']]

        self.assertTrue(len(links) == 1)

        # menu link should also have a link matching the name of the package.
        link = links[0]
        self.assertEqual(link.name, appbuilder_mitem['category'])
        self.assertEqual(link.childs[0].name, appbuilder_mitem['name'])

    def test_app_blueprints(self):
        from tests.plugins.test_plugin import bp

        # Blueprint should be present in the app
        self.assertTrue('test_plugin' in self.app.blueprints)
        self.assertEqual(self.app.blueprints['test_plugin'].name, bp.name)

    @unittest.skipIf(six.PY2, 'self.assertLogs not available for Python 2')
    @mock.patch('pkg_resources.iter_entry_points')
    def test_entrypoint_plugin_errors_dont_raise_exceptions(self, mock_ep_plugins):
        """
        Test that Airflow does not raise an Error if there is any Exception because of the
        Plugin.
        """
        from airflow.plugins_manager import load_entrypoint_plugins, import_errors

        mock_entrypoint = mock.Mock()
        mock_entrypoint.name = 'test-entrypoint'
        mock_entrypoint.module_name = 'test.plugins.test_plugins_manager'
        mock_entrypoint.load.side_effect = Exception('Version Conflict')
        mock_ep_plugins.return_value = [mock_entrypoint]

        with self.assertLogs("airflow.plugins_manager", level="ERROR") as log_output:
            load_entrypoint_plugins(pkg_resources.iter_entry_points('airflow.plugins'), [])
            received_logs = log_output.output[0]
            # Assert Traceback is shown too
            assert "Traceback (most recent call last):" in received_logs
            assert "Version Conflict" in received_logs
            assert "Failed to import plugin test-entrypoint" in received_logs
            assert ('test.plugins.test_plugins_manager', 'Version Conflict') in import_errors.items()
