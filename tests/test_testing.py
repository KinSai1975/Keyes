# -*- coding: utf-8 -*-
"""
    tests.testing
    ~~~~~~~~~~~~~

    Test client and more.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import pytest

import keyes

from keyes._compat import text_type


def test_environ_defaults_from_config():
    app = keyes.Keyes(__name__)
    app.testing = True
    app.config['SERVER_NAME'] = 'example.com:1234'
    app.config['APPLICATION_ROOT'] = '/foo'
    @app.route('/')
    def index():
        return keyes.request.url

    ctx = app.test_request_context()
    assert ctx.request.url == 'http://example.com:1234/foo/'
    with app.test_client() as c:
        rv = c.get('/')
        assert rv.data == b'http://example.com:1234/foo/'

def test_environ_defaults():
    app = keyes.Keyes(__name__)
    app.testing = True
    @app.route('/')
    def index():
        return keyes.request.url

    ctx = app.test_request_context()
    assert ctx.request.url == 'http://localhost/'
    with app.test_client() as c:
        rv = c.get('/')
        assert rv.data == b'http://localhost/'

def test_redirect_keep_session():
    app = keyes.Keyes(__name__)
    app.secret_key = 'testing'

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if keyes.request.method == 'POST':
            return keyes.redirect('/getsession')
        keyes.session['data'] = 'foo'
        return 'index'

    @app.route('/getsession')
    def get_session():
        return keyes.session.get('data', '<missing>')

    with app.test_client() as c:
        rv = c.get('/getsession')
        assert rv.data == b'<missing>'

        rv = c.get('/')
        assert rv.data == b'index'
        assert keyes.session.get('data') == 'foo'
        rv = c.post('/', data={}, follow_redirects=True)
        assert rv.data == b'foo'

        # This support requires a new Werkzeug version
        if not hasattr(c, 'redirect_client'):
            assert keyes.session.get('data') == 'foo'

        rv = c.get('/getsession')
        assert rv.data == b'foo'

def test_session_transactions():
    app = keyes.Keyes(__name__)
    app.testing = True
    app.secret_key = 'testing'

    @app.route('/')
    def index():
        return text_type(keyes.session['foo'])

    with app.test_client() as c:
        with c.session_transaction() as sess:
            assert len(sess) == 0
            sess['foo'] = [42]
            assert len(sess) == 1
        rv = c.get('/')
        assert rv.data == b'[42]'
        with c.session_transaction() as sess:
            assert len(sess) == 1
            assert sess['foo'] == [42]

def test_session_transactions_no_null_sessions():
    app = keyes.Keyes(__name__)
    app.testing = True

    with app.test_client() as c:
        with pytest.raises(RuntimeError) as e:
            with c.session_transaction() as sess:
                pass
        assert 'Session backend did not open a session' in str(e.value)

def test_session_transactions_keep_context():
    app = keyes.Keyes(__name__)
    app.testing = True
    app.secret_key = 'testing'

    with app.test_client() as c:
        rv = c.get('/')
        req = keyes.request._get_current_object()
        assert req is not None
        with c.session_transaction():
            assert req is keyes.request._get_current_object()

def test_session_transaction_needs_cookies():
    app = keyes.Keyes(__name__)
    app.testing = True
    c = app.test_client(use_cookies=False)
    with pytest.raises(RuntimeError) as e:
        with c.session_transaction() as s:
            pass
    assert 'cookies' in str(e.value)

def test_test_client_context_binding():
    app = keyes.Keyes(__name__)
    app.config['LOGGER_HANDLER_POLICY'] = 'never'
    @app.route('/')
    def index():
        keyes.g.value = 42
        return 'Hello World!'

    @app.route('/other')
    def other():
        1 // 0

    with app.test_client() as c:
        resp = c.get('/')
        assert keyes.g.value == 42
        assert resp.data == b'Hello World!'
        assert resp.status_code == 200

        resp = c.get('/other')
        assert not hasattr(keyes.g, 'value')
        assert b'Internal Server Error' in resp.data
        assert resp.status_code == 500
        keyes.g.value = 23

    try:
        keyes.g.value
    except (AttributeError, RuntimeError):
        pass
    else:
        raise AssertionError('some kind of exception expected')

def test_reuse_client():
    app = keyes.Keyes(__name__)
    c = app.test_client()

    with c:
        assert c.get('/').status_code == 404

    with c:
        assert c.get('/').status_code == 404

def test_test_client_calls_teardown_handlers():
    app = keyes.Keyes(__name__)
    called = []
    @app.teardown_request
    def remember(error):
        called.append(error)

    with app.test_client() as c:
        assert called == []
        c.get('/')
        assert called == []
    assert called == [None]

    del called[:]
    with app.test_client() as c:
        assert called == []
        c.get('/')
        assert called == []
        c.get('/')
        assert called == [None]
    assert called == [None, None]

def test_full_url_request():
    app = keyes.Keyes(__name__)
    app.testing = True

    @app.route('/action', methods=['POST'])
    def action():
        return 'x'

    with app.test_client() as c:
        rv = c.post('http://domain.com/action?vodka=42', data={'gin': 43})
        assert rv.status_code == 200
        assert 'gin' in keyes.request.form
        assert 'vodka' in keyes.request.args

def test_subdomain():
    app = keyes.Keyes(__name__)
    app.config['SERVER_NAME'] = 'example.com'
    @app.route('/', subdomain='<company_id>')
    def view(company_id):
        return company_id

    with app.test_request_context():
        url = keyes.url_for('view', company_id='xxx')

    with app.test_client() as c:
        response = c.get(url)

    assert 200 == response.status_code
    assert b'xxx' == response.data

def test_nosubdomain():
    app = keyes.Keyes(__name__)
    app.config['SERVER_NAME'] = 'example.com'
    @app.route('/<company_id>')
    def view(company_id):
        return company_id

    with app.test_request_context():
        url = keyes.url_for('view', company_id='xxx')

    with app.test_client() as c:
        response = c.get(url)

    assert 200 == response.status_code
    assert b'xxx' == response.data
