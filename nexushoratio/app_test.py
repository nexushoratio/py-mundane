"""Tests for app.py"""
import contextlib
import io
import unittest

from nexushoratio import app


class ArgparseAppParsingTest(unittest.TestCase):

    def test_no_args(self):
        my_app = app.ArgparseApp()
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args([])

        self.assertEqual(stdout.getvalue(), '')

    def test_dash_h(self):
        my_app = app.ArgparseApp()
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['-h'])

        self.assertRegex(stdout.getvalue(), r'Global flags:\n.*-h, --help')
        self.assertEqual(result.exception.code, 0)

    def test_dash_dash_help(self):
        my_app = app.ArgparseApp()
        stdout = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(stdout):
            my_app.parser.parse_args(['--help'])

        self.assertRegex(stdout.getvalue(), r'Global flags:\n.*-h, --help')
        self.assertEqual(result.exception.code, 0)

    def test_unknown_arg(self):
        my_app = app.ArgparseApp()
        stderr = io.StringIO()

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stderr(stderr):
            my_app.parser.parse_args(['-k'])

        self.assertRegex(
            stderr.getvalue(), r'error: unrecognized arguments: -k')
        self.assertEqual(result.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
