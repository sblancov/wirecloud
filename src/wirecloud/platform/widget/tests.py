# -*- coding: utf-8 -*-

# Copyright (c) 2012-2015 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of Wirecloud.

# Wirecloud is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Wirecloud is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Wirecloud.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os.path
import re

from django.conf import settings
from django.http import Http404
from django.test import TestCase
from mock import MagicMock, Mock, patch

from wirecloud.platform import plugins
from wirecloud.platform.widget.utils import fix_widget_code
from wirecloud.platform.widget.views import serve_showcase_media


# Avoid nose to repeat these tests (they are run through wirecloud/platform/tests/__init__.py)
__test__ = False


@patch('wirecloud.platform.core.plugins.get_version_hash', new=Mock(return_value='v1'))
class CodeTransformationTestCase(TestCase):

    tags = ('wirecloud-widget-module', 'wirecloud-widget-code-transformation', 'wirecloud-noselenium')

    XML_NORMALIZATION_RE = re.compile(b'>\\s+<')

    @classmethod
    def setUpClass(cls):
        if hasattr(settings, 'FORCE_DOMAIN'):
            cls.old_FORCE_DOMAIN = settings.FORCE_DOMAIN
        if hasattr(settings, 'FORCE_PROTO'):
            cls.old_FORCE_PROTO = settings.FORCE_PROTO

        settings.FORCE_DOMAIN = 'example.com'
        settings.FORCE_PROTO = 'http'
        cls.OLD_WIRECLOUD_PLUGINS = getattr(settings, 'WIRECLOUD_PLUGINS', None)

        settings.WIRECLOUD_PLUGINS = ()
        plugins.clear_cache()

        super(CodeTransformationTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'old_FORCE_DOMAIN'):
            settings.FORCE_DOMAIN = cls.old_FORCE_DOMAIN
        else:
            del settings.FORCE_DOMAIN

        if hasattr(cls, 'old_FORCE_PROTO'):
            settings.FORCE_PROTO = cls.old_FORCE_PROTO
        else:
            del settings.FORCE_PROTO

        settings.WIRECLOUD_PLUGINS = cls.OLD_WIRECLOUD_PLUGINS
        plugins.clear_cache()

        super(CodeTransformationTestCase, cls).tearDownClass()

    def read_file(self, *filename):
        f = open(os.path.join(os.path.dirname(__file__), *filename), 'rb')
        contents = f.read()
        f.close()

        return contents

    def test_unhandled_content_type(self):

        initial_code = b'plain text'
        final_code = fix_widget_code(initial_code, 'http://server.com/widget', 'text/plain', None, 'utf-8', False, {}, False, 'classic')
        self.assertEqual(final_code, initial_code)

    def test_empty_html(self):

        initial_code = b''
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'text/html', None, 'utf-8', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/html-empty-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_html_unclosed_tags(self):

        initial_code = self.read_file('test-data/html-unclosed-tags-initial.html')
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'text/html', None, 'utf-8', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/html-unclosed-tags-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_basic_html(self):
        initial_code = self.read_file('test-data/xhtml1-initial.html')
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'text/html', None, 'utf-8', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/xhtml1-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_basic_html_iso8859_15(self):
        initial_code = self.read_file('test-data/xhtml1-iso8859-15-initial.html')
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'text/html', None, 'iso-8859-15', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/xhtml1-iso8859-15-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_html_with_one_base_element(self):
        initial_code = self.read_file('test-data/xhtml4-initial.html')
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'text/html', None, 'utf-8', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/xhtml4-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_html_with_more_than_one_base_element(self):
        initial_code = self.read_file('test-data/xhtml4-extra-base-elements-initial.html')
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'text/html', None, 'utf-8', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/xhtml4-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_html_with_more_than_one_base_element_force_base(self):
        initial_code = self.read_file('test-data/xhtml4-extra-base-elements-initial.html')
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'text/html', None, 'utf-8', False, {}, True, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/xhtml4-forced-base-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_empty_xhtml(self):

        initial_code = b''
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'application/xhtml+xml', None, 'utf-8', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/xhtml-empty-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_xhtml_unclosed_tags(self):

        initial_code = self.read_file('test-data/xhtml-unclosed-tags-initial.html')
        self.assertRaises(Exception, fix_widget_code, initial_code, 'http://server.com/widget', 'application/xhtml+xml', None, 'utf-8', False, {}, False, 'classic')

    def test_basic_xhtml(self):
        initial_code = self.read_file('test-data/xhtml2-initial.html')
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'application/xhtml+xml', None, 'utf-8', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/xhtml2-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_basic_xhtml_iso8859_15(self):
        initial_code = self.read_file('test-data/xhtml2-iso8859-15-initial.html')
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'application/xhtml+xml', None, 'iso-8859-15', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/xhtml2-iso8859-15-expected.html')
        self.assertEqual(final_code, expected_code)

    def test_xhtml_without_head_element(self):
        initial_code = self.read_file('test-data/xhtml3-initial.html')
        final_code = self.XML_NORMALIZATION_RE.sub(b'><', fix_widget_code(initial_code, 'http://server.com/widget', 'application/xhtml+xml', None, 'utf-8', False, {}, False, 'classic')) + b'\n'
        expected_code = self.read_file('test-data/xhtml3-expected.html')
        self.assertEqual(final_code, expected_code)


class WidgetModuleTestCase(TestCase):

    tags = ('wirecloud-widget-module', 'wirecloud-noselenium')

    def build_mocks(self, resource_type='widget'):

        get_object_or_404_mock = Mock()
        resource_mock = Mock()
        resource_mock.resource_type.return_value = resource_type
        get_object_or_404_mock.return_value = resource_mock

        request_mock = Mock()
        request_mock.method = 'GET'

        return request_mock, get_object_or_404_mock, Mock()

    def test_mashup_path(self):

        request, get_object_or_404_mock, build_downloadfile_response_mock = self.build_mocks('mashup')

        with patch.multiple('wirecloud.platform.widget.views', get_object_or_404=get_object_or_404_mock, build_downloadfile_response=build_downloadfile_response_mock):
            self.assertRaises(Http404, serve_showcase_media, request, 'Wirecloud', 'Test', '1.0', 'js/file.js')
            self.assertEqual(build_downloadfile_response_mock.call_count, 0)

    def test_path_file_found(self):

        request, get_object_or_404_mock, build_downloadfile_response_mock = self.build_mocks()

        response_mock = Mock()
        response_mock.status_code = 200
        build_downloadfile_response_mock.return_value = response_mock

        with self.settings(USE_XSENDFILE=False):
            with patch.multiple('wirecloud.platform.widget.views', get_object_or_404=get_object_or_404_mock, build_downloadfile_response=build_downloadfile_response_mock):
                response = serve_showcase_media(request, 'Wirecloud', 'Test', '1.0', 'js/file.js')
                self.assertEqual(response, response_mock)

    def test_path_file_not_found(self):

        request, get_object_or_404_mock, build_downloadfile_response_mock = self.build_mocks()

        build_downloadfile_response_mock.side_effect = Http404()

        with patch.multiple('wirecloud.platform.widget.views', get_object_or_404=get_object_or_404_mock, build_downloadfile_response=build_downloadfile_response_mock):
            self.assertRaises(Http404, serve_showcase_media, request, 'Wirecloud', 'Test', '1.0', 'notfound.js')
            self.assertEqual(build_downloadfile_response_mock.call_count, 1)

    def test_path_outside_widget_folder(self):

        request, get_object_or_404_mock, build_downloadfile_response_mock = self.build_mocks()

        response_mock = MagicMock()
        response_mock.status_code = 302
        headers = {'Location': 'manage.py'}
        def set_header(key, value):
            headers[key] = value
        def get_header(key):
            return headers[key]
        response_mock.__setitem__.side_effect = set_header
        response_mock.__getitem__.side_effect = get_header
        build_downloadfile_response_mock.return_value = response_mock

        with self.settings(USE_XSENDFILE=False):
            with patch.multiple('wirecloud.platform.widget.views', get_object_or_404=get_object_or_404_mock):
                response = serve_showcase_media(request, 'Wirecloud', 'Test', '1.0', 'test/../../../../../../manage.py')
                self.assertEqual(response.status_code, 302)
                self.assertNotIn('..', response['Location'])
