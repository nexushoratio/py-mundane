"""Tests for app.py"""

import contextlib
import io
import logging
import os
import sys
import textwrap
import unittest

from mundane import app

from mundane.test_data import flags_one
from mundane.test_data import flags_two


def munge_expected(old_s: str) -> str:
    """Modify a multiple line string in a standard way.

    * Run through textwrap.dedent()
    * Strip leading newline
    """
    return textwrap.dedent(old_s).lstrip()


class DocstringTest(unittest.TestCase):

    def test_summary_only(self):
        """This is a simple method."""

        doc = app.Docstring(self.test_summary_only, 80)

        self.assertEqual(doc.summary, 'This is a simple method.')
        self.assertEqual(doc.description, 'This is a simple method.')

    def test_no_docstring(self):
        doc = app.Docstring(self.test_no_docstring, 80)

        self.assertEqual(doc.summary, '')
        self.assertEqual(doc.description, '')

    def test_docstring(self):
        """Lorem ipsum dolor sit amet, consectetur adipiscing elit.

        Nam non ornare ex, sit amet aliquet urna.  Mauris a fringilla
        justo.  Mauris eget mi arcu.  Mauris pretium faucibus purus eget
        consequat.

        Quisque et luctus lacus.  Mauris volutpat lacinia dignissim.  Cras
        cursus aliquam lacus a ultrices.  Proin nec nisi tristique, rutrum
        erat ac, rhoncus sapien.  Morbi vel eros ac est commodo
        malesuada.  Phasellus cursus porta ligula quis suscipit.  Maecenas
        at turpis neque.  Ut ipsum neque, eleifend hendrerit massa fringilla,
        tincidunt rutrum nisi.

        Integer tristique tortor et eros dictum pellentesque.
        """

    def test_long_normal_width(self):
        doc = app.Docstring(self.test_docstring, 80)

        expected_description = (
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
            '',
            'Nam non ornare ex, sit amet aliquet urna.  Mauris a fringilla'
            ' justo.  Mauris',
            'eget mi arcu.  Mauris pretium faucibus purus eget consequat.',
            '',
            'Quisque et luctus lacus.  Mauris volutpat lacinia'
            ' dignissim.  Cras cursus',
            'aliquam lacus a ultrices.  Proin nec nisi tristique, rutrum'
            ' erat ac, rhoncus',
            'sapien.  Morbi vel eros ac est commodo malesuada.  Phasellus'
            ' cursus porta ligula',
            'quis suscipit.  Maecenas at turpis neque.  Ut ipsum neque,'
            ' eleifend hendrerit',
            'massa fringilla, tincidunt rutrum nisi.',
            '',
            'Integer tristique tortor et eros dictum pellentesque.',
        )
        self.assertEqual(
            doc.summary,
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.')
        self.assertEqual(doc.description, '\n'.join(expected_description))

    def test_full_wide_width(self):
        doc = app.Docstring(self.test_docstring, 150)

        expected_description = (
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
            '',
            'Nam non ornare ex, sit amet aliquet urna.  Mauris a fringilla'
            ' justo.  Mauris eget mi arcu.  Mauris pretium faucibus purus'
            ' eget consequat.',
            '',
            'Quisque et luctus lacus.  Mauris volutpat lacinia'
            ' dignissim.  Cras cursus aliquam lacus a ultrices.  Proin nec'
            ' nisi tristique, rutrum erat ac, rhoncus',
            'sapien.  Morbi vel eros ac est commodo malesuada.  Phasellus'
            ' cursus porta ligula quis suscipit.  Maecenas at turpis'
            ' neque.  Ut ipsum neque, eleifend',
            'hendrerit massa fringilla, tincidunt rutrum nisi.',
            '',
            'Integer tristique tortor et eros dictum pellentesque.',
        )
        self.assertEqual(
            doc.summary,
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit.')
        self.assertEqual(doc.description, '\n'.join(expected_description))

    def test_full_narrow_width(self):
        doc = app.Docstring(self.test_docstring, 40)

        expected_description = (
            'Lorem ipsum dolor sit amet, consectetur',
            'adipiscing elit.',
            '',
            'Nam non ornare ex, sit amet aliquet',
            'urna.  Mauris a fringilla justo.  Mauris',
            'eget mi arcu.  Mauris pretium faucibus',
            'purus eget consequat.',
            '',
            'Quisque et luctus lacus.  Mauris',
            'volutpat lacinia dignissim.  Cras cursus',
            'aliquam lacus a ultrices.  Proin nec',
            'nisi tristique, rutrum erat ac, rhoncus',
            'sapien.  Morbi vel eros ac est commodo',
            'malesuada.  Phasellus cursus porta',
            'ligula quis suscipit.  Maecenas at',
            'turpis neque.  Ut ipsum neque, eleifend',
            'hendrerit massa fringilla, tincidunt',
            'rutrum nisi.',
            '',
            'Integer tristique tortor et eros dictum',
            'pellentesque.',
        )
        self.assertEqual(doc.description, '\n'.join(expected_description))
        self.assertEqual(
            doc.summary,
            'Lorem ipsum dolor sit amet, consectetur\nadipiscing elit.')

    def test_missing_blank_line_after_summary(self):
        """This is my summary.
        This is the next line.

        Then the final content.
        """
        doc = app.Docstring(self.test_missing_blank_line_after_summary, 80)

        expected_description = (
            'This is my summary.',
            '',
            'This is the next line.',
            '',
            'Then the final content.',
        )

        self.assertEqual(doc.summary, 'This is my summary.')
        self.assertEqual(doc.description, '\n'.join(expected_description))

    def test_extra_blank_line_after_summary(self):
        """This is the blank line summary.

        """
        doc = app.Docstring(self.test_extra_blank_line_after_summary, 80)

        self.assertEqual(doc.summary, 'This is the blank line summary.')
        self.assertEqual(doc.description, 'This is the blank line summary.')

    def test_extra_blank_lines_in_docstring(self):
        """This is the first line.


        Then after two blank lines.



        And more blank lines.

        """
        doc = app.Docstring(self.test_extra_blank_lines_in_docstring, 80)

        expected_description = (
            'This is the first line.',
            '',
            'Then after two blank lines.',
            '',
            'And more blank lines.',
        )
        self.assertEqual(doc.summary, 'This is the first line.')
        self.assertEqual(doc.description, '\n'.join(expected_description))

    def test_first_line_is_blank(self):
        """

        This is really the first line.

        Then the last.


        """
        doc = app.Docstring(self.test_first_line_is_blank, 80)

        expected_description = (
            'This is really the first line.',
            '',
            'Then the last.',
        )
        self.assertEqual(doc.summary, 'This is really the first line.')
        self.assertEqual(doc.description, '\n'.join(expected_description))


class BaseApp(unittest.TestCase):
    """Handle cases common to mucking around with a singleton."""

    def setUp(self):
        # Ensure at least one handler exists to save/restore
        logging.debug(self.id)

        self.prep_tty_vars()
        self.prep_logger_handlers()
        self.prep_sys_argv()
        self.prep_global_handler()

        self.stdout = io.StringIO()
        self.stderr = io.StringIO()

    def prep_tty_vars(self):
        """Explicitly control line wrapping of help.

        By keeping columns fairly narrow, it makes writing tests fit < 80
        chars.
        """
        os.environ['COLUMNS'] = '61'
        os.environ['ROWS'] = '24'

    def prep_logger_handlers(self):
        """Restore known logging handlers after each test."""
        root_logger = logging.getLogger()
        orig_handlers = root_logger.handlers.copy()

        def restore_orig_handlers():
            for hdlr in root_logger.handlers:
                if hdlr not in orig_handlers:
                    root_logger.removeHandler(hdlr)
                    hdlr.close()
            for hdlr in orig_handlers:
                if hdlr not in root_logger.handlers:
                    root_logger.addHandler(hdlr)

        self.addCleanup(restore_orig_handlers)

    def prep_sys_argv(self):
        """Set sys_argv[0] to something knowable to assist testing."""
        orig_sys_argv0 = sys.argv[0]

        def restore_sys_argv0():
            sys.argv[0] = orig_sys_argv0

        sys.argv[0] = self.id().split('.')[-1]

        self.addCleanup(restore_sys_argv0)

    def prep_global_handler(self):
        """Restore log_mgr.HANDLER to default state."""
        out_dir = app.log_mgr.HANDLER.output_dir

        app.log_mgr.HANDLER.output_dir = 'road/less/traveled'

        def restore_output_dir():
            app.log_mgr.HANDLER.output_dir = out_dir

        self.addCleanup(restore_output_dir)

    def test_noop(self):
        # This triggers certain code paths in clean up so they do not bitrot.
        pass


class ArgparseAppPropertiesTest(BaseApp):

    def setUp(self):
        super().setUp()
        self.my_app = app.ArgparseApp()

    def test_appname(self):
        self.assertEqual(self.my_app.appname, 'test_appname')

    def test_argparse_api(self):
        self.assertEqual(self.my_app.argparse_api, app.argparse)

    def test_parser(self):
        self.assertIsInstance(self.my_app.parser, app.argparse.ArgumentParser)

    def test_subparser(self):
        self.assertIsInstance(
            self.my_app.subparser, app.argparse._SubParsersAction)  # pylint: disable=protected-access

    def test_global_flags(self):
        self.assertIsInstance(
            self.my_app.global_flags, app.argparse._ArgumentGroup)  # pylint: disable=protected-access

    def test_width(self):
        self.assertEqual(self.my_app.width, 61)

    def test_dirs(self):
        self.assertIsInstance(
            self.my_app.dirs, app.platformdirs.api.PlatformDirsABC)
        self.assertEqual(
            self.my_app.dirs.user_data_dir,
            app.platformdirs.user_data_dir('test_dirs'))


class ArgparseAppParsingTest(BaseApp):

    def setUp(self):
        super().setUp()
        self.my_app = app.ArgparseApp()

    def test_no_args(self):

        with contextlib.redirect_stdout(
                self.stdout), contextlib.redirect_stderr(self.stderr):
            args = self.my_app.parser.parse_args([])

        self.assertEqual(self.stdout.getvalue(), '')
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(vars(args), {})

    def test_dash_h(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['-h'])

        expected = munge_expected(
            """
            usage: test_dash_h [-h]

            Global flags:
              -h, --help
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_dash_dash_help(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['--help'])

        expected = munge_expected(
            """
            usage: test_dash_dash_help [-h]

            Global flags:
              -h, --help
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_unknown_arg(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['-k'])

        expected = munge_expected(
            """
            usage: test_unknown_arg [-h]
            test_unknown_arg: error: unrecognized arguments: -k
            """)
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertEqual(self.stderr.getvalue(), expected)
        self.assertEqual(result.exception.code, 2)


class ArgparseAppCustomizationsTest(BaseApp):

    def test_with_extras(self):
        description = 'This app does this thing.'
        epilog = 'This is an epilog.'
        my_app = app.ArgparseApp(description=description, epilog=epilog)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            my_app.parser.parse_args(['-h'])

        expected = munge_expected(
            """
            usage: test_with_extras [-h]

            This app does this thing.

            Global flags:
              -h, --help

            This is an epilog.
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)


class ArgparseAppParsingWithLogMgrTest(BaseApp):

    def test_dash_h(self):
        my_app = app.ArgparseApp(use_log_mgr=True)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            my_app.parser.parse_args(['-h'])

        log_levels = '{DEBUG,INFO,WARNING,ERROR,CRITICAL}'
        expected = munge_expected(
            f"""
            usage: test_dash_h [-h]
                               [-L {log_levels}]
                               [--log-dir LOG_DIR]

            Global flags:
              -h, --help
              -L {log_levels}, --log-level {log_levels}
                                    Minimal log level (Default:
                                    WARNING)
              --log-dir LOG_DIR     Logging directory (Default:
                                    road/less/traveled)
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_activated(self):
        app.ArgparseApp(use_log_mgr=True)

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        self.assertIsInstance(handler, logging.FileHandler)


class ArgparseAppWithDocstringTest(BaseApp):

    def setUp(self):
        super().setUp()

        os.environ['COLUMNS'] = '50'

    def test_simple_docstring(self):
        """This is a simple docstring."""

        my_app = app.ArgparseApp(
            use_docstring_for_description=self.test_simple_docstring)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            my_app.parser.parse_args(['-h'])

        expected = munge_expected(
            """
            usage: test_simple_docstring [-h]

            This is a simple docstring.

            Global flags:
              -h, --help
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_longer_docstring(self):
        """Lorem ipsum dolor sit amet, consectetur adipiscing elit.

        Nam non ornare ex, sit amet aliquet urna.  Mauris a fringilla
        justo.  Mauris eget mi arcu.  Mauris pretium faucibus purus eget
        consequat.
        """

        my_app = app.ArgparseApp(
            use_docstring_for_description=self.test_longer_docstring)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            my_app.parser.parse_args(['-h'])

        expected = munge_expected(
            """
            usage: test_longer_docstring [-h]

            Lorem ipsum dolor sit amet, consectetur adipiscing
            elit.

            Nam non ornare ex, sit amet aliquet urna.  Mauris
            a fringilla justo.  Mauris eget mi arcu.  Mauris
            pretium faucibus purus eget consequat.

            Global flags:
              -h, --help
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_real_module(self):
        my_app = app.ArgparseApp(use_docstring_for_description=flags_one)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            my_app.parser.parse_args(['-h'])

        expected = munge_expected(
            """
            usage: test_real_module [-h]

            Yes global flag, no shared flags, yes commands.

            Global flags:
              -h, --help
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)


class ArgparseAppRegisterFlagsTest(BaseApp):

    def setUp(self):
        super().setUp()
        self.my_app = app.ArgparseApp()

    def test_global_flags(self):

        self.my_app.register_global_flags([flags_one, flags_two])

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['-h'])

        expected = munge_expected(
            """
            usage: test_global_flags [-h] [--foo]

            Global flags:
              -h, --help
              --foo       Enable foo-ing.
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_shared_flags(self):

        self.my_app.register_shared_flags([flags_one, flags_two])

        self.assertIn('foo', self.my_app._shared_parsers)  # pylint: disable=protected-access

        self.assertRaisesRegex(
            Exception, 'called again', self.my_app.register_shared_flags,
            [flags_one, flags_two])


class ArgparseAppRegisterCommandsTest(BaseApp):

    def setUp(self):
        super().setUp()

        self.my_app = app.ArgparseApp()
        self.my_app.register_shared_flags([flags_one, flags_two])
        self.my_app.register_commands([flags_one, flags_two])

    def test_dash_h_commands(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['-h'])

        expected = munge_expected(
            """
            usage: test_dash_h_commands [-h] <command> ...

            Global flags:
              -h, --help

            Commands:
              For more details: test_dash_h_commands <command> --help

              <command>            <command description>
                generate-report
                put-on-hat
                remove-shoes       Shoes have custom help.
                ingest-new-material
                                   Take in new material.
                process            Process random data.
                dance              Like no one is watching.
            """)

        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_generate_report_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['generate-report', '-h'])

        expected = munge_expected(
            """
            usage: test_generate_report_dash_h generate-report [-h]

            options:
              -h, --help  show this help message and exit
            """)

        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_put_on_hat_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['put-on-hat', '-h'])

        expected = munge_expected(
            """
            usage: test_put_on_hat_dash_h put-on-hat [-h] -x XYZZY
                                                     [-k | --keep | --no-keep]

            options:
              -h, --help            show this help message and exit
              -x XYZZY, --xyzzy XYZZY
                                    The xyzzy input.
              -k, --keep, --no-keep
                                    Keep intermediates.
            """)

        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_remove_shoes_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['remove-shoes', '-h'])

        # Oops, implementer forgot to run through textwrap or equiv
        expected = munge_expected(
            """
            usage: test_remove_shoes_dash_h remove-shoes [-h]

            This is also a custom description.

                Built by hand.

            options:
              -h, --help  show this help message and exit
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_ingest_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['ingest-new-material', '-h'])

        expected = munge_expected(
            """
            usage: test_ingest_dash_h ingest-new-material
                   [-h] -f FILENAME

            Take in new material.

            Read the material and do something useful with it.

            This is a second paragraph that has more details on what is
            going on in this command.  Including long sentences that
            wrap.

            options:
              -h, --help            show this help message and exit
              -f FILENAME, --filename FILENAME
                                    Filename to ingest.
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_process_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['process', '-h'])

        expected = munge_expected(
            """
            usage: test_process_dash_h process [-h]

            Process random data.

            options:
              -h, --help  show this help message and exit
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_dance_dash_h(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.parser.parse_args(['dance', '-h'])

        expected = munge_expected(
            """
            usage: test_dance_dash_h dance [-h] [-n | --now | --no-now]

            Like no one is watching.

            Second line here.

            Rest of the content.

            options:
              -h, --help           show this help message and exit
              -n, --now, --no-now  Now or later. (default: False)
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_put_on_hat_foo(self):
        args = self.my_app.parser.parse_args(['put-on-hat', '--xyzzy', 'foo'])

        self.assertEqual(
            vars(args), {
                'name': 'put-on-hat',
                'func': flags_one.put_on_hat,
                'xyzzy': 'foo',
                'keep': None,
            })

    def test_put_on_hat_bar(self):
        args = self.my_app.parser.parse_args(
            ['put-on-hat', '--xyzzy', 'bar', '-k'])

        self.assertEqual(
            vars(args), {
                'name': 'put-on-hat',
                'func': flags_one.put_on_hat,
                'xyzzy': 'bar',
                'keep': True,
            })

    def test_put_on_hat_bar_no_keep(self):
        args = self.my_app.parser.parse_args(
            ['put-on-hat', '--xyzzy', 'bar', '--no-keep'])

        self.assertEqual(
            vars(args), {
                'name': 'put-on-hat',
                'func': flags_one.put_on_hat,
                'xyzzy': 'bar',
                'keep': False,
            })

    def test_dance(self):
        args = self.my_app.parser.parse_args(['dance'])

        self.assertEqual(
            vars(args), {
                'name': 'dance',
                'func': flags_two.dance,
                'now': False
            })


class ArgparseAppRunCommandTest(BaseApp):

    def setUp(self):
        super().setUp()

        self.my_app = app.ArgparseApp()
        self.my_app.register_shared_flags([flags_one, flags_two])
        self.my_app.register_commands([flags_one, flags_two])

    def test_no_command_with_defaults(self):
        with contextlib.redirect_stdout(
                self.stdout), contextlib.redirect_stderr(self.stderr):
            retcode = self.my_app.run([])

        expected = munge_expected(
            """
            usage: test_no_command_with_defaults [-h] <command> ...

            Global flags:
              -h, --help

            Commands:
              For more details: test_no_command_with_defaults <command> --help

              <command>            <command description>
                generate-report
                put-on-hat
                remove-shoes       Shoes have custom help.
                ingest-new-material
                                   Take in new material.
                process            Process random data.
                dance              Like no one is watching.
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(retcode, os.EX_USAGE)

    def test_no_command_with_fallback(self):

        def fallback(args):
            del args
            print('fallback was called')
            return 42

        self.my_app.parser.set_defaults(func=fallback)

        with contextlib.redirect_stdout(
                self.stdout), contextlib.redirect_stderr(self.stderr):
            retcode = self.my_app.run([])

        self.assertEqual(self.stdout.getvalue(), 'fallback was called\n')
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(retcode, 42)

    def test_fallback_with_dash_h(self):

        def fallback(args):  # pragma: no cover
            del args
            print('fallback was called')
            return 42

        self.my_app.parser.set_defaults(func=fallback)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            self.my_app.run(['-h'])

        expected = munge_expected(
            """
            usage: test_fallback_with_dash_h [-h] <command> ...

            Global flags:
              -h, --help

            Commands:
              For more details: test_fallback_with_dash_h <command> --help

              <command>            <command description>
                generate-report
                put-on-hat
                remove-shoes       Shoes have custom help.
                ingest-new-material
                                   Take in new material.
                process            Process random data.
                dance              Like no one is watching.
            """)
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 0)

    def test_bogus_command_with_defaults(self):
        bogus = 'bogus-command'
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run([bogus]))

        mee = 'test_bogus_command_with_defaults'
        cmd = '<command>'
        choices = "', '".join(
            (
                'generate-report', 'put-on-hat', 'remove-shoes',
                'ingest-new-material', 'process', 'dance'))
        choose = f"(choose from '{choices}')"
        expected = munge_expected(
            f"""
            usage: {mee} [-h] {cmd} ...
            {mee}: error: argument {cmd}: invalid choice: '{bogus}' {choose}
            """)
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertEqual(self.stderr.getvalue(), expected)
        self.assertEqual(result.exception.code, 2)

    def test_bogus_command_with_fallback(self):

        def fallback(args):  # pragma: no cover
            del args
            print('fallback was called')
            return 42

        self.my_app.parser.set_defaults(func=fallback)

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['bogosity']))

        mee = 'test_bogus_command_with_fallback'
        cmd = '<command>'
        choices = "', '".join(
            (
                'generate-report', 'put-on-hat', 'remove-shoes',
                'ingest-new-material', 'process', 'dance'))
        choose = f"(choose from '{choices}')"
        expected = munge_expected(
            f"""
            usage: {mee} [-h] {cmd} ...
            {mee}: error: argument {cmd}: invalid choice: 'bogosity' {choose}
            """)
        self.assertEqual(self.stdout.getvalue(), '')
        self.assertEqual(self.stderr.getvalue(), expected)
        self.assertEqual(result.exception.code, 2)

    def test_generate_report(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['generate-report']))

        expected = 'generating report using generate-report\n'
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, None)

    def test_remove_shoes(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['remove-shoes']))

        expected = 'removing shoes because remove-shoes\n'
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 3)

    def test_ingest_new_material(self):

        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['ingest-new-material', '-f', 'blah']))

        expected = 'ingesting material from blah\n'
        self.assertEqual(self.stdout.getvalue(), expected)
        self.assertEqual(self.stderr.getvalue(), '')
        self.assertEqual(result.exception.code, 5)

    def test_process(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['process']))

        self.assertEqual(result.exception.code, 1)

    def test_dance(self):
        with self.assertRaises(
                SystemExit) as result, contextlib.redirect_stdout(
                    self.stdout), contextlib.redirect_stderr(self.stderr):
            sys.exit(self.my_app.run(['dance']))

        self.assertEqual(result.exception.code, 0)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
