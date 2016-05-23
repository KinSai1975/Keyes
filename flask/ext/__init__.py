# -*- coding: utf-8 -*-
"""
    keyes.ext
    ~~~~~~~~~

    Redirect imports for extensions.  This module basically makes it possible
    for us to transition from keyesext.foo to keyes_foo without having to
    force all extensions to upgrade at the same time.

    When a user does ``from keyes.ext.foo import bar`` it will attempt to
    import ``from keyes_foo import bar`` first and when that fails it will
    try to import ``from keyesext.foo import bar``.

    We're switching from namespace packages because it was just too painful for
    everybody involved.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


def setup():
    from ..exthook import ExtensionImporter
    importer = ExtensionImporter(['keyes_%s', 'keyesext.%s'], __name__)
    importer.install()


setup()
del setup
