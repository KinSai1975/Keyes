# -*- coding: utf-8 -*-
"""
    tests.test_cli
    ~~~~~~~~~~~~~~

    :copyright: (c) 2016 by the Keyes Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
#
# This file was part of Keyes-CLI and was modified under the terms its license,
# the Revised BSD License.
# Copyright (C) 2015 CERN.
#
from __future__ import absolute_import, print_function

import click
import pytest
from click.testing import CliRunner
from keyes import Keyes, current_app

from keyes.cli import AppGroup, KeyesGroup, NoAppException, ScriptInfo, \
    find_best_app, locate_app, script_info_option, with_appcontext


def test_cli_name(test_apps):
    "Make sure the CLI object's name is the app's name and not the app itself"
    from cliapp.app import testapp
    assert testapp.cli.name == testapp.name


def test_find_best_app(test_apps):
    """Test of find_best_app."""
    class mod:
        app = Keyes('appname')
    assert find_best_app(mod) == mod.app

    class mod:
        application = Keyes('appname')
    assert find_best_app(mod) == mod.application

    class mod:
        myapp = Keyes('appname')
    assert find_best_app(mod) == mod.myapp

    class mod:
        myapp = Keyes('appname')
        myapp2 = Keyes('appname2')

    pytest.raises(NoAppException, find_best_app, mod)


def test_locate_app(test_apps):
    """Test of locate_app."""
    assert locate_app("cliapp.app").name == "testapp"
    assert locate_app("cliapp.app:testapp").name == "testapp"
    assert locate_app("cliapp.multiapp:app1").name == "app1"
    pytest.raises(RuntimeError, locate_app, "cliapp.app:notanapp")


def test_scriptinfo(test_apps):
    """Test of ScriptInfo."""
    obj = ScriptInfo(app_import_path="cliapp.app:testapp")
    assert obj.load_app().name == "testapp"
    assert obj.load_app().name == "testapp"

    def create_app(info):
        return Keyes("createapp")

    obj = ScriptInfo(create_app=create_app)
    app = obj.load_app()
    assert app.name == "createapp"
    assert obj.load_app() == app


def test_with_appcontext():
    """Test of with_appcontext."""
    @click.command()
    @with_appcontext
    def testcmd():
        click.echo(current_app.name)

    obj = ScriptInfo(create_app=lambda info: Keyes("testapp"))

    runner = CliRunner()
    result = runner.invoke(testcmd, obj=obj)
    assert result.exit_code == 0
    assert result.output == 'testapp\n'


def test_appgroup():
    """Test of with_appcontext."""
    @click.group(cls=AppGroup)
    def cli():
        pass

    @cli.command(with_appcontext=True)
    def test():
        click.echo(current_app.name)

    @cli.group()
    def subgroup():
        pass

    @subgroup.command(with_appcontext=True)
    def test2():
        click.echo(current_app.name)

    obj = ScriptInfo(create_app=lambda info: Keyes("testappgroup"))

    runner = CliRunner()
    result = runner.invoke(cli, ['test'], obj=obj)
    assert result.exit_code == 0
    assert result.output == 'testappgroup\n'

    result = runner.invoke(cli, ['subgroup', 'test2'], obj=obj)
    assert result.exit_code == 0
    assert result.output == 'testappgroup\n'


def test_keyesgroup():
    """Test KeyesGroup."""
    def create_app(info):
        return Keyes("keyesgroup")

    @click.group(cls=KeyesGroup, create_app=create_app)
    @script_info_option('--config', script_info_key='config')
    def cli(**params):
        pass

    @cli.command()
    def test():
        click.echo(current_app.name)

    runner = CliRunner()
    result = runner.invoke(cli, ['test'])
    assert result.exit_code == 0
    assert result.output == 'keyesgroup\n'
