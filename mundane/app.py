"""Give an app reasonable startup defaults.

To use this module, simply define a 'main' function that instantiates
ArgparseApp(), sets up flags, and run.

def main() -> int:
    my_app = app.ArgparseApp()
    my_app.register_global_flags([module1, module2, ..., moduleN])
    my_app.register_shared_flags([module1, module2, ..., moduleN])
    my_app.register_commands([module1, module2, ..., moduleN])

    # Do any other set-up
    ...

    sys.exit(my_app.run())

if __name__ == '__main__':
    main()
"""

import argparse
import functools
import inspect
import logging
import os
import resource
import shutil
import textwrap
import types
import typing

import humanize
import platformdirs

from mundane import log_mgr


class ArgparseKwargs(typing.TypedDict, total=False):
    """Exists to make typing happy."""
    prog: str
    usage: str | None
    epilog: str | None
    formatter_class: 'argparse._FormatterClass'
    fromfile_prefix_chars: str | None
    add_help: bool
    allow_abbrev: bool
    description: str | None


class Docstring:
    """A reflowed docstring.

    Given any object with a __doc__ property, reflow the docstring to a given
    width.

    The instance has two properties: summary and description.
    """

    def __init__(self, obj: typing.Any, width: int):
        """Reflow the docstring.

        Args:
          obj: Any object with a docstring (module, function, etc).
          width: How wide the result should be.
        """
        self._doc = inspect.getdoc(obj)
        self._width = width
        self._summary = None
        self._description = None

    @property
    def summary(self):
        """The first line of the docstring, reflowed."""
        if self._summary is None:
            self._process()
        return self._summary

    @property
    def description(self):
        """Full docstring, reflowed."""
        if self._description is None:
            self._process()
        return self._description

    def _process(self):
        """Perform the actual split/reflow of the docstring."""
        self._summary = ''
        self._description = ''
        description_parts = list()

        def paragraphs(content):
            split = content.split('\n')
            yield textwrap.fill(split.pop(0).strip(), width=self._width)

            current = list()
            for item in split:
                stripped = item.strip()
                if stripped:
                    current.append(stripped)
                else:
                    if current:
                        yield textwrap.fill(
                            ' '.join(current), width=self._width)
                        current.clear()
            if current:
                yield textwrap.fill(' '.join(current), width=self._width)

        if self._doc:
            for para in paragraphs(self._doc):
                if not self._summary:
                    self._summary = para
                description_parts.append(para)

        self._description = '\n\n'.join(description_parts)


CommandFunc: typing.TypeAlias = typing.Callable[[argparse.Namespace], int]
NamespaceHook: typing.TypeAlias = typing.Callable[[argparse.Namespace], None]


class ArgparseApp:
    """Facilitate creating an argparse based application.

    This class attempts to make it easier to build applications using argparse
    for argument processing by providing a framework for a common approach,
    without taking away any of the abilities of argparse.  A basic
    understanding of the argparse module will be useful.

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
    * Execute the command the user requested by calling the run() method

    Since this is just a thin wrapper around argparse, everything can be
    fine-tuned as you move along.

    def main() -> int:
        my_app = app.ArgparseApp()
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
    contain an attribute named "func" with the CommandFunc signature.

    Generally this is done via the register_command() method, but may be done
    so directly as well via the parser property and its set_defaults() method.
    Specifically, this is necessary when subcommands are not used.
    """

    GLOBAL_FLAGS = 'Global flags'

    def __init__(
            self,
            use_log_mgr: bool = False,
            use_docstring_for_description: typing.Any | None = None,
            **kwargs: typing.Unpack[ArgparseKwargs]):
        """Initialize with the application.

        Args:
          use_log_mgr: Automatically add log_mgr's global flags and activate
            its logging configuration.
          use_docstring_for_description: Any object with a docstring (module,
            function, etc).  Will be the initial source for the description
            kwarg passed to ArgumentParser().
          kwargs: Passed directly to ArgumentParser().
        """
        parser_args: ArgparseKwargs = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'add_help': False,
        }
        if use_docstring_for_description:
            parser_args['description'] = Docstring(
                use_docstring_for_description, self.width).description

        parser_args.update(typing.cast(ArgparseKwargs, kwargs))

        self._parser = argparse.ArgumentParser(**parser_args)
        self._global_flags = self._parser.add_argument_group(
            self.GLOBAL_FLAGS)
        self._global_flags.add_argument('-h', '--help', action='help')
        self._shared_parsers: dict[str, argparse.ArgumentParser] = dict()
        self._after_parse_hooks: list[NamespaceHook] = list()

        if use_log_mgr:
            log_mgr.activate(self.appname, self.dirs.user_log_dir)
            self.register_global_flags([log_mgr])

    @property
    def appname(self) -> str:
        """The name for this app."""
        return self._parser.prog

    @property
    def argparse_api(self) -> types.ModuleType:
        """Return the argparse module as a convenience."""
        return argparse

    @property
    def parser(self) -> argparse.ArgumentParser:
        """The main parser for this class."""
        return self._parser

    @functools.cached_property
    def subparser(self) -> argparse._SubParsersAction:
        """The top-level command subparser for this class."""
        return self.new_subparser(self._parser)

    @property
    def global_flags(self) -> argparse._ArgumentGroup:
        """An argparse.ArgumentParser().add_argument_group() instance.

        Module hooks should use this property to add additional global flags.

        my_app.global_flags.add_argument(...)
        """
        return self._global_flags

    @functools.cached_property
    def width(self) -> int:
        """Width of the current terminal.

        Used internally when formatting help.
        """
        return shutil.get_terminal_size().columns

    @functools.cached_property
    def dirs(self) -> platformdirs.api.PlatformDirsABC:
        """Accessor for a consistent PlatformsDirs."""
        return platformdirs.PlatformDirs(appname=self.appname)

    def new_subparser(
            self,
            parser: argparse.ArgumentParser) -> argparse._SubParsersAction:
        """Attach a new subparser to an existing parser.

        This allows for sub-subcommands.
        """
        return parser.add_subparsers(
            title='Commands',
            dest='name',
            metavar='<command>',
            help='<command description>',
            description='For more details: %(prog)s <command> --help')

    def new_shared_parser(self, name: str) -> argparse.ArgumentParser | None:
        """Register and return a new parser iff it does not already exist.

        Typically a module's mundane_shared_flags hook will call this to
        create flags shared across modules.

        foo_parser = my_app.new_shared_parser('foo')
        if foo_parser:
          foo_parser.add_argument(...)
          foo_parser.add_argument(...)
        else:
          raise Exception('Someone already used "foo" as a parser name!')

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
        """Returns a shared parser iff it already exists, else None.

        Typically a module's mundane_commands hook will call this to get an
        existing shared parser so that flags can be consistent between
        commands.

        foo_parser = my_app.get_shared_parser('foo')
        if foo_parser:
          my_app.register_command(..., parents=[foo_parser])
        else:
          raise Exception('The parser "foo" was not shared!')
        """
        return self._shared_parsers.get(name)

    def register_after_parse_hook(self, func: NamespaceHook) -> None:
        """Register a function to be called after parsing flags.

        This method is typically called from any module's hook that this class
        calls.

        These hooks are called in the order they were registered after flags
        are parsed and before the selected command is executed.

        They can be used for a variety of things:

        * Complex multi-flag validation that is difficult to do with basic
          argparse
        * Removing properties instead of using default=argparse.SUPPRESS
        * Adding properties, perhaps based on other flags, such as a database
          connection singleton

        Args:
            func: The function to register.
        """
        self._after_parse_hooks.append(func)

    def register_command(
            self,
            func: CommandFunc,
            subparser=None,
            **kwargs) -> argparse.ArgumentParser:
        """Register a specific command.

        This method is typically called by a module's mundane_commands() hook.
        It will register the supplied function as a new command using the name
        of the function and help text extracted from the function's docstring.

        Underscores in the function name are turned into a minus symbol for
        easier use on the command line.

        A new parser is returned and the function may then add flags using the
        standard add_argument() method.


        parser = my_app.register_command(cool_command, parents=[foo_parser])
        parser.add_argument(...)
        parser.add_argument(...)

        my_app.register_command(uncool_command)


        Args:
            func: The function to register.
            subparser: The command will be attached to this subparser.
            kwargs: Passed directly to add_parser()

        Returns:
            The result of add_parser() filled with information extracted from
            the function.
        """
        if subparser is None:
            subparser = self.subparser

        name = func.__name__.replace('_', '-')
        docstring = Docstring(func, self.width)

        parser_args = {
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'help': docstring.summary,
            'description': docstring.description,
        }
        parser_args.update(kwargs)

        parser = subparser.add_parser(name, **parser_args)
        parser.set_defaults(func=func)

        return parser

    def _register_module_via_hooks(
            self, hook_name: str, modules: typing.Iterable[types.ModuleType]):
        """Implements processing of modules to maybe execute a hook."""
        for module in modules:
            register_func = getattr(module, hook_name, None)
            if register_func:
                register_func(self)

    def register_global_flags(
            self, modules: typing.Iterable[types.ModuleType]):
        """Register global flags by calling 'MODULE.mundane_global_flags()'.

        Global flags are typically used for setting things like verbosity,
        databases, or other things shared between most commands.

        Each module is checked in turn for the existence of the hook
        'mundane_global_flags'.  If it exists, it is called with a single
        argument: this instance.

        Of usual interest to 'mundane_global_flags' is the property
        'global_flags'.  The hook should invoke the 'add_argument()' method as
        normal with argparse based code.

        If flag order matters, then use an ordered iterable (e.g., list,
        tuple).

        Args:
            modules: The modules to process.
        """
        self._register_module_via_hooks('mundane_global_flags', modules)

    def register_shared_flags(
            self, modules: typing.Iterable[types.ModuleType]):
        """Register shared flags by calling 'MODULE.mundane_shared_flags()'.

        When using applications with commands, sometimes it is nice to use the
        same flags in multiple locations.  This allows for consistency in
        naming, constraints, and help strings.  When the mundane_commands()
        hook is executed, they may use any registered shared flags as a
        parent for the command they will register.

        Each module is checked in turn for the existence of the hook
        'mundane_shared_flags'.  If it exists, it is called with a single
        argument: this instance.

        Of usual interest to 'mundane_shared_flags' are the property
        'argparse_api', and method 'new_shared_parser'.

        Args:
            modules: The modules to process.
        """
        self._register_module_via_hooks('mundane_shared_flags', modules)

    def register_commands(self, modules: typing.Iterable[types.ModuleType]):
        """Register commands by calling 'MODULE.mundane_commands()'.

        Some applications may wish to implement subcommands where each command
        may have its own set of flags.  This method facilitates this by
        providing an entry point for registering these commands.

        Each module is checked in turn for the existence of the hook
        'mundane_commands'.  If it exists, it is called with a single
        argument: this instance.

        Of usual interest to 'mundane_commands' are the methods
        'get_shared_parser' and 'register_command'.  For each function the
        module wants to register as a command, it will call
        register_command that will provide useful defaults and return a parser
        that can then add flags as expected using the add_argument() method.

        Args:
            modules: The modules to process.
        """
        self._register_module_via_hooks('mundane_commands', modules)

    def run(self, argv: list[str] | None = None) -> int:
        """Execute the selected function."""
        args = self.parser.parse_args(argv)

        for hook in self._after_parse_hooks:
            hook(args)

        ret = os.EX_USAGE
        if hasattr(args, 'func'):
            logging.debug('Calling %s with %s', args.func, args)
            ret = args.func(args)
            logging.debug(
                'Max memory used: %s',
                humanize.naturalsize(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
            logging.debug('Finished. (%d)', ret or 0)
        else:
            self.parser.print_help()

        return ret
