# -*- coding: utf-8 -*-
"""
    tests.appctx
    ~~~~~~~~~~~~

    Tests the application context.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import keyes


def test_basic_url_generation():
    app = keyes.Keyes(__name__)
    app.config['SERVER_NAME'] = 'localhost'
    app.config['PREFERRED_URL_SCHEME'] = 'https'

    @app.route('/')
    def index():
        pass

    with app.app_context():
        rv = keyes.url_for('index')
        assert rv == 'https://localhost/'

def test_url_generation_requires_server_name():
    app = keyes.Keyes(__name__)
    with app.app_context():
        with pytest.raises(RuntimeError):
            keyes.url_for('index')

def test_url_generation_without_context_fails():
    with pytest.raises(RuntimeError):
        keyes.url_for('index')

def test_request_context_means_app_context():
    app = keyes.Keyes(__name__)
    with app.test_request_context():
        assert keyes.current_app._get_current_object() == app
    assert keyes._app_ctx_stack.top is None

def test_app_context_provides_current_app():
    app = keyes.Keyes(__name__)
    with app.app_context():
        assert keyes.current_app._get_current_object() == app
    assert keyes._app_ctx_stack.top is None

def test_app_tearing_down():
    cleanup_stuff = []
    app = keyes.Keyes(__name__)
    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    with app.app_context():
        pass

    assert cleanup_stuff == [None]

def test_app_tearing_down_with_previous_exception():
    cleanup_stuff = []
    app = keyes.Keyes(__name__)
    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    try:
        raise Exception('dummy')
    except Exception:
        pass

    with app.app_context():
        pass

    assert cleanup_stuff == [None]

def test_app_tearing_down_with_handled_exception():
    cleanup_stuff = []
    app = keyes.Keyes(__name__)
    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    with app.app_context():
        try:
            raise Exception('dummy')
        except Exception:
            pass

    assert cleanup_stuff == [None]

def test_app_ctx_globals_methods():
    app = keyes.Keyes(__name__)
    with app.app_context():
        # get
        assert keyes.g.get('foo') is None
        assert keyes.g.get('foo', 'bar') == 'bar'
        # __contains__
        assert 'foo' not in keyes.g
        keyes.g.foo = 'bar'
        assert 'foo' in keyes.g
        # setdefault
        keyes.g.setdefault('bar', 'the cake is a lie')
        keyes.g.setdefault('bar', 'hello world')
        assert keyes.g.bar == 'the cake is a lie'
        # pop
        assert keyes.g.pop('bar') == 'the cake is a lie'
        with pytest.raises(KeyError):
            keyes.g.pop('bar')
        assert keyes.g.pop('bar', 'more cake') == 'more cake'
        # __iter__
        assert list(keyes.g) == ['foo']

def test_custom_app_ctx_globals_class():
    class CustomRequestGlobals(object):
        def __init__(self):
            self.spam = 'eggs'
    app = keyes.Keyes(__name__)
    app.app_ctx_globals_class = CustomRequestGlobals
    with app.app_context():
        assert keyes.render_template_string('{{ g.spam }}') == 'eggs'

def test_context_refcounts():
    called = []
    app = keyes.Keyes(__name__)
    @app.teardown_request
    def teardown_req(error=None):
        called.append('request')
    @app.teardown_appcontext
    def teardown_app(error=None):
        called.append('app')
    @app.route('/')
    def index():
        with keyes._app_ctx_stack.top:
            with keyes._request_ctx_stack.top:
                pass
        env = keyes._request_ctx_stack.top.request.environ
        assert env['werkzeug.request'] is not None
        return u''
    c = app.test_client()
    res = c.get('/')
    assert res.status_code == 200
    assert res.data == b''
    assert called == ['request', 'app']
