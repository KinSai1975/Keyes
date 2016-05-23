# -*- coding: utf-8 -*-
"""
    tests.subclassing
    ~~~~~~~~~~~~~~~~~

    Test that certain behavior of keyes can be customized by
    subclasses.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import keyes
from logging import StreamHandler

from keyes._compat import StringIO


def test_suppressed_exception_logging():
    class SuppressedKeyes(keyes.Keyes):
        def log_exception(self, exc_info):
            pass

    out = StringIO()
    app = SuppressedKeyes(__name__)
    app.logger_name = 'keyes_tests/test_suppressed_exception_logging'
    app.logger.addHandler(StreamHandler(out))

    @app.route('/')
    def index():
        1 // 0

    rv = app.test_client().get('/')
    assert rv.status_code == 500
    assert b'Internal Server Error' in rv.data

    err = out.getvalue()
    assert err == ''
