# -*- coding: utf-8 -*-

# core modules
from pkg_resources import resource_filename
from tempfile import mkstemp, mkdtemp
import os
import shutil
import unittest

# 3rd party modules
from click.testing import CliRunner

# internal modules
from androguard.cli import entry_points


def get_apks():
    """Get a list of APKs for testing scripts"""
    for root, _, files in os.walk(resource_filename('androguard', '..')):
        for f in files:
            if f == 'multidex.apk':
                # This file does not have a manifest, hence everything fails
                continue
            if f.endswith('.apk') and 'signing' not in root:
                yield os.path.join(root, f)


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

    def test_axml_basic_call_by_positional_argument(self):
        axml_path = resource_filename('androguard',
                                      '../examples/axml/AndroidManifest.xml')
        _, output_path = mkstemp(prefix='androguard_', suffix='decoded.txt')
        runner = CliRunner()
        arguments = ['axml', axml_path, '-o', output_path]
        result = runner.invoke(entry_points.entry_point,
                               arguments)
        assert result.exit_code == 0, arguments
        os.remove(output_path)

    def test_axml_basic_call_by_input_argument(self):
        axml_path = resource_filename('androguard',
                                      '../examples/axml/AndroidManifest.xml')
        _, output_path = mkstemp(prefix='androguard_', suffix='decoded.txt')
        runner = CliRunner()
        arguments = ['axml', '-i', axml_path, '-o', output_path]
        result = runner.invoke(entry_points.entry_point,
                               arguments)
        assert result.exit_code == 0, arguments
        os.remove(output_path)

    def test_axml_error_call_two_arguments(self):
        axml_path = resource_filename('androguard',
                                      '../examples/axml/AndroidManifest.xml')
        _, output_path = mkstemp(prefix='androguard_', suffix='decoded.txt')
        runner = CliRunner()
        arguments = ['axml', '-i', axml_path,
                     '-o', output_path,
                     axml_path]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 1, arguments
        os.remove(output_path)

    def test_axml_error_call_no_arguments(self):
        _, output_path = mkstemp(prefix='androguard_', suffix='decoded.txt')
        runner = CliRunner()
        arguments = ['axml', '-o', output_path]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 1, arguments
        os.remove(output_path)

    def test_arsc_basic_call_positional_apk(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['arsc', apk_path]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 0, arguments

    def test_arsc_error_filetype_py(self):
        runner = CliRunner()
        dex_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'classes.dex')
        arguments = ['arsc', dex_path]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 1, arguments

    def test_arsc_basic_call_keyword(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['arsc', '-i', apk_path]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 0, arguments

    def test_arsc_basic_call_list_packages(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['arsc', apk_path, '--list-packages']
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 0, arguments

    def test_arsc_basic_call_list_locales(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['arsc', apk_path, '--list-locales']
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 0, arguments

    def test_arsc_basic_call_list_types(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['arsc', apk_path, '--list-types']
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 0, arguments

    def test_arsc_error_two_arguments(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['arsc', apk_path, '-i', apk_path]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 1, arguments

    def test_arsc_basic_id_resolve(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['arsc', apk_path, '--id', '7F030000']
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 0, arguments

    def test_arsc_error_id_resolve(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['arsc', apk_path, '--id', 'sdlkfjsdlkf']
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 1, arguments

    def test_arsc_error_id_not_resolve(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['arsc', apk_path, '--id', '12345678']
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 1, arguments

    def test_arsc_error_no_arguments(self):
        runner = CliRunner()
        arguments = ['arsc']
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 1, arguments

    def test_arsc_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point, ['arsc', '--help'])
        assert result.exit_code == 0

    def test_cg_basic(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        arguments = ['--debug', 'cg', apk_path]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 0

    def test_cg_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point, ['cg', '--help'])
        assert result.exit_code == 0

    def test_decompile_basic_positional(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        output_dir = mkdtemp(prefix='androguard_test_')
        result = runner.invoke(entry_points.entry_point,
                               ['decompile', apk_path, '-o', output_dir])
        assert result.exit_code == 0
        # Cleanup:
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            shutil.rmtree(output_dir)

    def test_decompile_basic_input(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        output_dir = mkdtemp(prefix='androguard_test_')
        result = runner.invoke(entry_points.entry_point,
                               ['decompile', '-i', apk_path, '-o', output_dir])
        assert result.exit_code == 0
        # Cleanup:
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            shutil.rmtree(output_dir)

    def test_decompile_error_two_arguments(self):
        runner = CliRunner()
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        output_dir = mkdtemp(prefix='androguard_test_')
        arguments = ['decompile', '-i', apk_path, apk_path, '-o', output_dir]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 1, arguments
        # Cleanup:
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            shutil.rmtree(output_dir)

    def test_decompile_error_no_arguments(self):
        runner = CliRunner()
        output_dir = mkdtemp(prefix='androguard_test_')
        arguments = ['decompile', '-o', output_dir]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 1, arguments
        # Cleanup:
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            shutil.rmtree(output_dir)

    def test_decompile_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point,
                               ['decompile', '--help'])
        assert result.exit_code == 0

    def test_sign_basic(self):
        apk_path = resource_filename('androguard',
                                     '../examples/dalvik/test/bin/'
                                     'Test-debug.apk')
        runner = CliRunner()
        arguments = ['sign', apk_path]
        result = runner.invoke(entry_points.entry_point, arguments)
        assert result.exit_code == 0

    def test_sign_help(self):
        runner = CliRunner()
        result = runner.invoke(entry_points.entry_point, ['sign', '--help'])
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

    def test_androsign(self):
        runner = CliRunner()
        for apk in get_apks():
            print("testing for {}".format(apk))
            arguments = ['sign', apk]
            result = runner.invoke(entry_points.entry_point, arguments)
            assert result.exit_code == 0

    def test_androaxml(self):
        runner = CliRunner()
        for apk in get_apks():
            print("testing for {}".format(apk))
            arguments = ['axml', apk]
            result = runner.invoke(entry_points.entry_point, arguments)
            assert result.exit_code == 0

    def test_androarsc(self):
        runner = CliRunner()
        # TODO could check here more stuff for example returned lists etc
        for apk in get_apks():
            print("testing for {}".format(apk))
            arguments = ['arsc', apk]
            result = runner.invoke(entry_points.entry_point, arguments)
            assert result.exit_code == 0

            arguments = ['arsc', "-t", "string", apk]
            result = runner.invoke(entry_points.entry_point, arguments)
            assert result.exit_code == 0

            arguments = ['arsc', "--list-packages", apk]
            result = runner.invoke(entry_points.entry_point, arguments)
            assert result.exit_code == 0

            arguments = ['arsc', "--list-types", apk]
            result = runner.invoke(entry_points.entry_point, arguments)
            assert result.exit_code == 0

            arguments = ['arsc', "--list-locales", apk]
            result = runner.invoke(entry_points.entry_point, arguments)
            assert result.exit_code == 0
