"""Give an app reasonable startup defaults.

To use this module, simply define a 'main' function with a single
'app_parser' argument and add the following to the end of your main
module:

if __name__ == '__main__':
    sys.exit(app.run(main))


The main function is expected to take an argparse.ArgumentParser object
and use that as a parents= parameter to another instance.
"""

import argparse
import datetime
import inspect
import logging
import os
import pwd
import socket
import resource
import shutil
import sys
import tempfile
import textwrap
import types
import typing

import humanize


class LogAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """Callback action to tweak log settings during flag parsing."""

    def __call__(
            self,
            parser,
            namespace,
            values,
            option_string=None):  # pragma: no cover
        numeric_level = getattr(logging, values.upper())
        logging.getLogger().setLevel(numeric_level)


class ArgparseApp:
    """Facilitate creating an argparse based application.

    This class attempts to make it easier to build applications using argparse
    for argument processing by providing a framework for a common approach
    without taking away any of argparse's abilities.  A basic understanding of
    the argparse module will be useful.

    We will try to use the term "flags" rather than "options".  As the
    argparse documentation points out: "users expect options to be optional".
    However, for many applications it is easier to remember what flag goes
    with a parameter rather than what order they go in.  So, they are
    required, just the order is malleable.  Also, sometimes, say when working
    interactively at a command prompt, it might be easier to supply a value
    LAST.

    Take the pretend command, nebulous, which can do many strange and wondrous
    things, but in this case we are interested in the "ingest" feature.  It
    might work like this:

    nebulous ingest DATA DESTINATION

    You have many things to load, but you want to run a command after each
    thing before continuing.  This could be easily scripting by making DATA a
    variable, but another option might be to do something like:

    nebulous ingest --dest=DESTINATION --data=DATA-1
    ... post processing checks ...
    # Use "uparrow" "backspace" "2" to get:
    nebulous ingest --dest=DESTINATION --data=DATA-2

    and so on... using flags (not options), makes it easier to arrange the
    parameters as needed.

    To create an application, do the following:
    * Instantiate an instance of ArgparseApp
    * Add any global flags by calling the register_global_flags() method
    * Add any parsers that may be shared between command by calling the
      register_shared_flags() method
    * Add any commands by calling the register_commands() method
    * Execute the command the use requested by calling the run() method

    Since this is just a thin wrapper around argparse, everything can be
    fine-tuned as you move along.

    def main() -> int:
        my_app = mundane.ArgparseApp()
        my_app.register_global_flags([module1, module2, ..., moduleN])
        my_app.register_shared_flags([module1, module2, ..., moduleN])
        my_app.register_commands([module1, module2, ..., moduleN])

        # Do any other set-up
        ...

        sys.exit(my_app.run())

    if __name__ == '__main__':
        main()


    The magic comes from a simple expectation:
    * The Namespace object returned from the resulting parse_args() will
    contain an attribute named "func" with the signature:
        typing.Callable[argparse.Namespace, int]

    Generally this is done by the register_command() method, but may be done
    so directly as well via the parser property and its set_defaults() method.
    """

    GLOBAL_FLAGS = 'Global flags'

    def __init__(self):
        """Initialize with the callback function.

        Args:
          main: The function to call when executed via run().
        """
        self._parser = argparse.ArgumentParser(add_help=False)
        self._global_flags = self._parser.add_argument_group(
            self.GLOBAL_FLAGS)
        self._global_flags.add_argument('-h', '--help', action='help')
        self._shared_parsers = dict()
        self._subparser = None
        self._width = None

    @property
    def argparse_api(self) -> types.ModuleType:
        """Return argparse as a convenience."""
        return argparse

    @property
    def global_flags(self):
        """An argparse.ArgumentParser().add_argument_group() instance."""
        return self._global_flags

    @property
    def parser(self) -> argparse.ArgumentParser:
        """The main parser for this class."""
        return self._parser

    @property
    def subparser(self) -> argparse.ArgumentParser:
        """The command subparser for this class."""
        if not self._subparser:
            self._subparser = self._parser.add_subparsers(
                title='Commands',
                dest='name',
                metavar='<command>',
                help='<command description>',
                description='For more details: %(prog)s <command> --help')
        return self._subparser

    @property
    def width(self):
        """Width of the current terminal."""
        if not self._width:
            self._width = shutil.get_terminal_size().columns
        return self._width

    def new_shared_parser(self, name: str) -> argparse.ArgumentParser | None:
        """Create and register a new parser iff it does not already exist.

        Args:
            name: The key to find this parser.

        Returns:
            The parser, only if a new one is created.
        """
        if name not in self._shared_parsers:
            self._shared_parsers[name] = argparse.ArgumentParser(
                add_help=False)
            return self._shared_parsers[name]
        return None

    def get_shared_parser(self, name: str) -> argparse.ArgumentParser | None:
        """Returns a parser iff it already exists, else None ."""
        return self._shared_parsers.get(name)

    def _register_module_stuff(
            self, func_name: str, modules: list[types.ModuleType]):
        """Implements processing of modules to maybe execute a function."""
        for module in modules:
            register_func = getattr(module, func_name, None)
            if register_func:
                register_func(self)

    def register_global_flags(
            self, modules: typing.Iterable[types.ModuleType]):
        """Register global flags by calling 'MODULE.mundane_global_flags()'.

        Global flags are typically used for setting things like verbosity,
        databases, or other things shared between commands.

        Each module is checked in turn for the existence of the function
        'mundane_global_flags'.  If it exists, it is called with a single
        argument: this instance.

        Of usual interest to 'mundane_global_flags' is the property
        'global_flags', which was created by
        ArgumentParser().add_argument_group().  The function should invoke the
        'add_argument()' method as normal with argparse based code.

        If flag order matters, then use an ordered iterable (e.g., list,
        tuple).

        Args:
            modules: The modules to process.

        """
        self._register_module_stuff('mundane_global_flags', modules)

    def register_shared_flags(
            self, modules: typing.Iterable[types.ModuleType]):
        """Register shared flags by calling 'MODULE.mundane_shared_flags()'.

        When using applications with commands, sometimes is nice to use the
        same flags in multiple locations, for consistency in things naming,
        constraints, and help strings.  When the mundane_commands() method is
        executed, they may use any registered shared flags as a parent for the
        subparser they will create.

        Each module is checked in turn for the existence of the function
        'mundane_shared_flags'.  If it exists, it is called with a single
        argument: this instance.

        Of usual interest to 'mundane_shared_flags' are the properties
        'argparse' which is just module of the same name, and 'shared_flags',
        which is a mapping of strings to ArgumentParser.

        Args:
            modules: The modules to process.

        """
        self._register_module_stuff('mundane_shared_flags', modules)

    def register_commands(self, modules: typing.Iterable[types.ModuleType]):
        """Register commands by calling 'MODULE.mundane_commands()'.

        Some applications may wish to implement subcommands where each command
        may have its own set of flags.  This method facilitates this by
        providing an entry point for registering these commands.

        Each module is checked in turn for the existence of the function
        'mundane_commands'.  If it exists, it is called with a single
        argument: this instance.

        Of usual interest to 'mundane_commands' are the property
        'shared_flags' and method 'register_command'.  For each function the
        module wants to register as a command, it will call the
        register_command that will include useful defaults and return a parser
        that can then add flags as expected using the add_argument() method.

        Args:
            modules: The modules to process.

        """
        self._register_module_stuff('mundane_commands', modules)

    def register_command(
            self, func: typing.Callable[argparse.Namespace, int],
            **kwargs) -> argparse.ArgumentParser:
        """Register a specific command.

        This method is called by a module's mundane_commands() function.  It
        will register the supplied function as a new command using the name of
        the function and help text extracted from the functions docstring.

        Underscores in the function name are turned into a minus symbol for
        easier use on the command line.

        A new parser is returned and the function may then add flags using the
        standard add_argument() method.

        Args:
            func: The function to register.
            kwargs: Passed directly to add_parser()

        Returns:
            The result of add_parser() filled with information extracted from
            the function.

        """
        docstring = inspect.getdoc(func)
        name = func.__name__.replace('_', '-')
        description_parts = list()
        summary = None
        body = None
        if docstring:
            split = docstring.split('\n', 1)
            summary = split.pop(0).strip()
            description_parts.append(summary)
            if split:
                body = '\n\n'.join(
                    textwrap.fill(x, width=self.width)
                    for x in split[-1].strip().split('\n\n'))
                description_parts.append(body)

        description = '\n\n'.join(description_parts)

        parser_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'help': summary,
            'description': description,
        }
        parser_args.update(kwargs)

        parser = self.subparser.add_parser(name, **parser_args)
        parser.set_defaults(func=func)

        return parser

    def run(self) -> int:
        """Execute the selected function."""
        args = self.parser.parse_args()
        ret = os.EX_USAGE
        try:
            logging.debug('Calling %s with %s', args.func, args)
            ret = args.func(args)
            logging.debug(
                'Max memory used: %s',
                humanize.naturalsize(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
            logging.debug('Finished. (%d)', ret or 0)
        except AttributeError:
            self.parser.print_help()

        return ret


# pylint: disable=duplicate-code
def run(func):  # pragma: no cover
    """Main entry point for application.

    Args:
        func: callback function - Signature should be
            typing.Callable[[argparse.ArgumentParser], int].

    Returns:
        Return value of func.
    """
    parser = argparse.ArgumentParser(add_help=False)
    group = parser.add_argument_group('Global flags')
    group.add_argument('-h', '--help', action='help')
    group.add_argument(
        '-L',
        '--loglevel',
        action=LogAction,
        help='Log level',
        default=argparse.SUPPRESS,
        choices=('debug', 'info', 'warning', 'error'))

    # argv[0] -> argv[0].$HOST.$USER.$DATETIME.$PID

    progname = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

    short_filename = f'{progname}.log'
    long_filename = (
        f'{short_filename}.{socket.gethostname()}'
        f'.{pwd.getpwuid(os.getuid())[0]}.{now}.{os.getpid()}')

    long_pathname = os.path.join(tempfile.gettempdir(), long_filename)
    short_pathname = os.path.join(tempfile.gettempdir(), short_filename)

    log_format = (
        '%(levelname).1s%(asctime)s: %(filename)s:%(lineno)d'
        '(%(funcName)s)] {%(name)s} %(message)s')
    logging.basicConfig(
        level=logging.INFO, format=log_format, filename=long_pathname)
    logging.info('Started.')
    # best effort on symlink
    try:
        os.unlink(short_pathname)
    except OSError:
        pass
    os.symlink(long_pathname, short_pathname)
    ret = func(parser)
    logging.info(
        'Max memory used: %s',
        humanize.naturalsize(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    logging.info('Finished. (%d)', ret or 0)
    return ret
