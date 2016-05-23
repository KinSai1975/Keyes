# -*- coding: utf-8 -*-
"""
    tests.ext
    ~~~~~~~~~~~~~~~~~~~

    Tests the extension import thing.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import sys
import pytest

try:
    from imp import reload as reload_module
except ImportError:
    reload_module = reload

from keyes._compat import PY2


@pytest.fixture(autouse=True)
def importhook_setup(monkeypatch, request):
    # we clear this out for various reasons.  The most important one is
    # that a real keyesext could be in there which would disable our
    # fake package.  Secondly we want to make sure that the keyesext
    # import hook does not break on reloading.
    for entry, value in list(sys.modules.items()):
        if (
            entry.startswith('keyes.ext.') or
            entry.startswith('keyes_') or
            entry.startswith('keyesext.') or
            entry == 'keyesext'
        ) and value is not None:
            monkeypatch.delitem(sys.modules, entry)
    from keyes import ext
    reload_module(ext)

    # reloading must not add more hooks
    import_hooks = 0
    for item in sys.meta_path:
        cls = type(item)
        if cls.__module__ == 'keyes.exthook' and \
           cls.__name__ == 'ExtensionImporter':
            import_hooks += 1
    assert import_hooks == 1

    def teardown():
        from keyes import ext
        for key in ext.__dict__:
            assert '.' not in key

    request.addfinalizer(teardown)


@pytest.fixture
def newext_simple(modules_tmpdir):
    x = modules_tmpdir.join('keyes_newext_simple.py')
    x.write('ext_id = "newext_simple"')


@pytest.fixture
def oldext_simple(modules_tmpdir):
    keyesext = modules_tmpdir.mkdir('keyesext')
    keyesext.join('__init__.py').write('\n')
    keyesext.join('oldext_simple.py').write('ext_id = "oldext_simple"')


@pytest.fixture
def newext_package(modules_tmpdir):
    pkg = modules_tmpdir.mkdir('keyes_newext_package')
    pkg.join('__init__.py').write('ext_id = "newext_package"')
    pkg.join('submodule.py').write('def test_function():\n    return 42\n')


@pytest.fixture
def oldext_package(modules_tmpdir):
    keyesext = modules_tmpdir.mkdir('keyesext')
    keyesext.join('__init__.py').write('\n')
    oldext = keyesext.mkdir('oldext_package')
    oldext.join('__init__.py').write('ext_id = "oldext_package"')
    oldext.join('submodule.py').write('def test_function():\n'
                                      '    return 42')


@pytest.fixture
def keyesext_broken(modules_tmpdir):
    ext = modules_tmpdir.mkdir('keyes_broken')
    ext.join('b.py').write('\n')
    ext.join('__init__.py').write('import keyes.ext.broken.b\n'
                                  'import missing_module')


def test_keyesext_new_simple_import_normal(newext_simple):
    from keyes.ext.newext_simple import ext_id
    assert ext_id == 'newext_simple'


def test_keyesext_new_simple_import_module(newext_simple):
    from keyes.ext import newext_simple
    assert newext_simple.ext_id == 'newext_simple'
    assert newext_simple.__name__ == 'keyes_newext_simple'


def test_keyesext_new_package_import_normal(newext_package):
    from keyes.ext.newext_package import ext_id
    assert ext_id == 'newext_package'


def test_keyesext_new_package_import_module(newext_package):
    from keyes.ext import newext_package
    assert newext_package.ext_id == 'newext_package'
    assert newext_package.__name__ == 'keyes_newext_package'


def test_keyesext_new_package_import_submodule_function(newext_package):
    from keyes.ext.newext_package.submodule import test_function
    assert test_function() == 42


def test_keyesext_new_package_import_submodule(newext_package):
    from keyes.ext.newext_package import submodule
    assert submodule.__name__ == 'keyes_newext_package.submodule'
    assert submodule.test_function() == 42


def test_keyesext_old_simple_import_normal(oldext_simple):
    from keyes.ext.oldext_simple import ext_id
    assert ext_id == 'oldext_simple'


def test_keyesext_old_simple_import_module(oldext_simple):
    from keyes.ext import oldext_simple
    assert oldext_simple.ext_id == 'oldext_simple'
    assert oldext_simple.__name__ == 'keyesext.oldext_simple'


def test_keyesext_old_package_import_normal(oldext_package):
    from keyes.ext.oldext_package import ext_id
    assert ext_id == 'oldext_package'


def test_keyesext_old_package_import_module(oldext_package):
    from keyes.ext import oldext_package
    assert oldext_package.ext_id == 'oldext_package'
    assert oldext_package.__name__ == 'keyesext.oldext_package'


def test_keyesext_old_package_import_submodule(oldext_package):
    from keyes.ext.oldext_package import submodule
    assert submodule.__name__ == 'keyesext.oldext_package.submodule'
    assert submodule.test_function() == 42


def test_keyesext_old_package_import_submodule_function(oldext_package):
    from keyes.ext.oldext_package.submodule import test_function
    assert test_function() == 42


def test_keyesext_broken_package_no_module_caching(keyesext_broken):
    for x in range(2):
        with pytest.raises(ImportError):
            import keyes.ext.broken


def test_no_error_swallowing(keyesext_broken):
    with pytest.raises(ImportError) as excinfo:
        import keyes.ext.broken

    assert excinfo.type is ImportError
    if PY2:
        message = 'No module named missing_module'
    else:
        message = 'No module named \'missing_module\''
    assert str(excinfo.value) == message
    assert excinfo.tb.tb_frame.f_globals is globals()

    # reraise() adds a second frame so we need to skip that one too.
    # On PY3 we even have another one :(
    next = excinfo.tb.tb_next.tb_next
    if not PY2:
        next = next.tb_next

    import os.path
    assert os.path.join('keyes_broken', '__init__.py') in \
        next.tb_frame.f_code.co_filename
