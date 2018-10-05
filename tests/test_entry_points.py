# -*- coding: utf-8 -*-

# core modules
from pkg_resources import resource_filename
from tempfile import mkstemp
import os
import unittest

# 3rd party modules
from click.testing import CliRunner

# internal modules
from androguard.cli import entry_points


class EntryPointsTest(unittest.TestCase):
    def test_entry_point_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point, ['--help'])
        assert result.exit_code == 0

    def test_axml_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point,
                               ['axml', '--help'])
        assert result.exit_code == 0

    def test_axml_basic_call(self):
        axml_path = resource_filename('androguard',
                                      '../examples/axml/AndroidManifest.xml')
        _, output_path = mkstemp(prefix='androguard_', suffix='decoded.txt')
        runner = CliRunner()
        arguments = ['axml', axml_path, '-o', output_path]
        result = runner.invoke(entry_points.entry_point,
                               arguments)
        assert result.exit_code == 0, arguments
        os.remove(output_path)

    def test_arsc_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point,
                               ['arsc', '--help'])
        assert result.exit_code == 0

    def test_cg_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point,
                               ['cg', '--help'])
        assert result.exit_code == 0

    def test_decompile_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point,
                               ['decompile', '--help'])
        assert result.exit_code == 0

    def test_sign_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point,
                               ['sign', '--help'])
        assert result.exit_code == 0

    def test_gui_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point,
                               ['gui', '--help'])
        assert result.exit_code == 0

    def test_analyze_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point,
                               ['analyze', '--help'])
        assert result.exit_code == 0

