# -*- coding: utf-8 -*-
"""
    tests.views
    ~~~~~~~~~~~

    Pluggable views.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import keyes
import keyes.views

from werkzeug.http import parse_set_header

def common_test(app):
    c = app.test_client()

    assert c.get('/').data == b'GET'
    assert c.post('/').data == b'POST'
    assert c.put('/').status_code == 405
    meths = parse_set_header(c.open('/', method='OPTIONS').headers['Allow'])
    assert sorted(meths) == ['GET', 'HEAD', 'OPTIONS', 'POST']

def test_basic_view():
    app = keyes.Keyes(__name__)

    class Index(keyes.views.View):
        methods = ['GET', 'POST']
        def dispatch_request(self):
            return keyes.request.method

    app.add_url_rule('/', view_func=Index.as_view('index'))
    common_test(app)

def test_method_based_view():
    app = keyes.Keyes(__name__)

    class Index(keyes.views.MethodView):
        def get(self):
            return 'GET'
        def post(self):
            return 'POST'

    app.add_url_rule('/', view_func=Index.as_view('index'))

    common_test(app)

def test_view_patching():
    app = keyes.Keyes(__name__)

    class Index(keyes.views.MethodView):
        def get(self):
            1 // 0
        def post(self):
            1 // 0

    class Other(Index):
        def get(self):
            return 'GET'
        def post(self):
            return 'POST'

    view = Index.as_view('index')
    view.view_class = Other
    app.add_url_rule('/', view_func=view)
    common_test(app)

def test_view_inheritance():
    app = keyes.Keyes(__name__)

    class Index(keyes.views.MethodView):
        def get(self):
            return 'GET'
        def post(self):
            return 'POST'

    class BetterIndex(Index):
        def delete(self):
            return 'DELETE'

    app.add_url_rule('/', view_func=BetterIndex.as_view('index'))
    c = app.test_client()

    meths = parse_set_header(c.open('/', method='OPTIONS').headers['Allow'])
    assert sorted(meths) == ['DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST']

def test_view_decorators():
    app = keyes.Keyes(__name__)

    def add_x_parachute(f):
        def new_function(*args, **kwargs):
            resp = keyes.make_response(f(*args, **kwargs))
            resp.headers['X-Parachute'] = 'awesome'
            return resp
        return new_function

    class Index(keyes.views.View):
        decorators = [add_x_parachute]
        def dispatch_request(self):
            return 'Awesome'

    app.add_url_rule('/', view_func=Index.as_view('index'))
    c = app.test_client()
    rv = c.get('/')
    assert rv.headers['X-Parachute'] == 'awesome'
    assert rv.data == b'Awesome'

def test_implicit_head():
    app = keyes.Keyes(__name__)

    class Index(keyes.views.MethodView):
        def get(self):
            return keyes.Response('Blub', headers={
                'X-Method': keyes.request.method
            })

    app.add_url_rule('/', view_func=Index.as_view('index'))
    c = app.test_client()
    rv = c.get('/')
    assert rv.data == b'Blub'
    assert rv.headers['X-Method'] == 'GET'
    rv = c.head('/')
    assert rv.data == b''
    assert rv.headers['X-Method'] == 'HEAD'

def test_explicit_head():
    app = keyes.Keyes(__name__)

    class Index(keyes.views.MethodView):
        def get(self):
            return 'GET'
        def head(self):
            return keyes.Response('', headers={'X-Method': 'HEAD'})

    app.add_url_rule('/', view_func=Index.as_view('index'))
    c = app.test_client()
    rv = c.get('/')
    assert rv.data == b'GET'
    rv = c.head('/')
    assert rv.data == b''
    assert rv.headers['X-Method'] == 'HEAD'

def test_endpoint_override():
    app = keyes.Keyes(__name__)
    app.debug = True

    class Index(keyes.views.View):
        methods = ['GET', 'POST']
        def dispatch_request(self):
            return keyes.request.method

    app.add_url_rule('/', view_func=Index.as_view('index'))

    with pytest.raises(AssertionError):
        app.add_url_rule('/', view_func=Index.as_view('index'))

    # But these tests should still pass. We just log a warning.
    common_test(app)
