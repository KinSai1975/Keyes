# -*- coding: utf-8 -*-
"""
    tests.deprecations
    ~~~~~~~~~~~~~~~~~~

    Tests deprecation support. Not used currently.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import keyes


class TestRequestDeprecation(object):

    def test_request_json(self, catch_deprecation_warnings):
        """Request.json is deprecated"""
        app = keyes.Keyes(__name__)
        app.testing = True

        @app.route('/', methods=['POST'])
        def index():
            assert keyes.request.json == {'spam': 42}
            print(keyes.request.json)
            return 'OK'

        with catch_deprecation_warnings() as captured:
            c = app.test_client()
            c.post('/', data='{"spam": 42}', content_type='application/json')

        assert len(captured) == 1

    def test_request_module(self, catch_deprecation_warnings):
        """Request.module is deprecated"""
        app = keyes.Keyes(__name__)
        app.testing = True

        @app.route('/')
        def index():
            assert keyes.request.module is None
            return 'OK'

        with catch_deprecation_warnings() as captured:
            c = app.test_client()
            c.get('/')

        assert len(captured) == 1
