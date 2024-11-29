"""This is the nebulous application.

It is a demo for using the mundane library and should cover most features.

The text below exists to demonstrate how the help output is reflowed to match
the terminal width.  Experiment with resizing the terminal or setting the
environment variable COLUMNS to different values.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam sagittis
mattis risus, vel ultricies est dictum in. Pellentesque malesuada neque lacus,
a commodo nisl condimentum vel. Praesent pretium, tortor eget convallis
congue, metus augue posuere velit, eget tempus sapien ipsum a felis. Fusce et
eleifend enim. Vestibulum vel pharetra orci. Ut vehicula bibendum ante nec
lacinia. Nullam vestibulum hendrerit libero, ac congue purus vulputate
ultrices.

Nulla gravida ullamcorper ante in mattis. Praesent malesuada justo a dignissim
pellentesque. Mauris feugiat dignissim libero eu volutpat. Sed feugiat ipsum
id posuere rhoncus. Nulla odio sapien, sollicitudin quis lobortis vel, ornare
in risus. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices
posuere cubilia curae; Aenean ipsum est, elementum vitae ultricies eget,
tempus euismod nisl. Proin vel cursus mi.
"""

from __future__ import annotations

# The log manager that mundane provides defaults to writing to a unique file
# on each invocation.
import logging
import sys
import typing

from mundane import app

if typing.TYPE_CHECKING:
    import argparse


class Error(Exception):
    """Base module exception."""


def mundane_global_flags(ctx: app.ArgparseApp):
    """Register global flags."""
    ctx.global_flags.add_argument(
        '--db-dir',
        help='Database directory (Default: %(default)s)',
        action='store',
        default=ctx.dirs.user_data_dir)

    # This is a good place to add a hook as well.
    ctx.register_after_parse_hook(hook_one)
    ctx.register_after_parse_hook(init_db)
    ctx.register_after_parse_hook(hook_three)


def mundane_shared_flags(ctx: app.ArgparseApp):
    """Register shared flags."""

    # Nothing magical about the 'req_' prefix, just convention.
    parser = ctx.new_shared_parser('req_file')
    if parser:
        parser.add_argument(
            '-f',
            '--file',
            action='store',
            required=True,
            help='A filename to process.')
        parser.add_argument(
            '-u', '--unused', action='store', help='This flag is not used.')
    else:
        raise Error('Oh, dear!  Someone stole our parser name!')


def mundane_commands(ctx: app.ArgparseApp):
    """Register commands."""
    req_file = ctx.get_shared_parser('req_file')
    if not req_file:
        raise Error('Oh, my!  No one registered our file parser!')

    ctx.register_command(info)
    ctx.register_command(ingest, parents=[req_file])

    # Demonstrate how a local flag or configuration could be reused across
    # commands.
    clean_args = ('-i', '--item')
    clean_kwargs = {
        'action': 'store',
        'help': 'An item to clean.',
    }
    clean_flags = ctx.argparse_api.ArgumentParser(add_help=False)
    clean_flags.add_argument(*clean_args, required=True, **clean_kwargs)
    parser = ctx.register_command(clean, parents=[clean_flags])

    ctx.register_command(del_, name='del')
    ctx.register_command(two_words)

    parser = ctx.register_command(general)
    subparser = ctx.new_subparser(parser)
    ctx.register_command(status, subparser=subparser)
    ctx.register_command(hostname, subparser=subparser)
    ctx.register_command(permissions, subparser=subparser)

    # Demonstrate how to have a subcommand that only displays usage.
    parser = ctx.register_command(roger, usage_only=True)
    subparser = ctx.new_subparser(parser)
    ctx.register_command(roger, subparser=subparser)


def hook_one(args: argparse.Namespace):
    """Demonstrate the order hooks are called."""
    logging.info('args: %s', args)


def hook_three(args: argparse.Namespace):
    """Demonstrate the order hooks are called."""
    logging.info('args: %s', args)


def init_db(args: argparse.Namespace):
    """This hook will modify args.

    A database connection will be added as "dbc" and the "db_dir" flag will be
    consumed.
    """
    logging.info('args: %s', args)

    # The name of the command that will be executed.  Empty if the user just
    # asked for help.  For this example, do not create the database.
    if args.name:
        args.dbc = f'A pretend database connection in {args.db_dir}.'
        del args.db_dir


def info(args: argparse.Namespace) -> int:
    """List some important information.

    Note that this command has a multiline docstring.  It will be shown when
    the --help flag is used.
    """
    logging.debug('debug output from info: %s', args)
    print(f'{args=}')

    level = logging.getLogger().level
    name = logging.getLevelName(level)
    print(f'Current logging level: {name}')

    return 0


def ingest(args: argparse.Namespace) -> int:
    """Consume some information and push it into the database."""

    if args.unused:
        print(
            'I said, --unused is not used.  Why did you'
            f' pass in "{args.unused}"?')
    else:
        print(
            f'I will read "{args.file}"'
            f' and put the content into "{args.dbc}".')

    return 0


def clean(args: argparse.Namespace) -> int:
    """Clean an item (maybe).

    Be sure to check the error code.
    """
    known = ('rock', 'paper', 'scissors')

    ret = 0
    if args.item in known:
        print('Scrub.  Scrub.  Scrub.')
        print(f'The {args.item} is now clean.')
    else:
        print(f'Actually, I do not know how to clean {args.item}.')
        ret = 1

    return ret


def del_(args: argparse.Namespace) -> int:
    """Delete the world."""
    print('The world is deleted.')

    return 0


def two_words(args: argparse.Namespace) -> int:
    """Print out two words."""
    print('Two words.')
    print(
        'But, note that the command has a "-" but the function name has "_".')

    return 0


def general(args: argparse.Namespace) -> int:
    """An nmcli like general command."""

    # This is the default command
    return status(args)


def status(args: argparse.Namespace) -> int:
    """An nmcli like status command."""
    print('This is the overall status.')

    return 0


def hostname(args: argparse.Namespace) -> int:
    """An nmcli like hostname command."""
    print('Hostname is: unknown')

    return 1


def permissions(args: argparse.Namespace) -> int:
    """An nmcli like permissions command."""
    print('This would be a table of permissions.')

    return 0


def roger(args: argparse.Namespace) -> int:
    """Acknowledge Roger, but only the second time."""

    print('Roger, Roger.')

    return 0


def main() -> int:
    """A nebulous app."""
    # Use this module for the help output.
    nebulous_app = app.ArgparseApp(
        use_log_mgr=True, use_docstring_for_description=sys.modules[__name__])

    # Typically this would be a number of imported modules, but for this demo,
    # we will just use ourself.
    modules = (sys.modules[__name__],)

    # There is nothing that requires the same modules be used below, just
    # tradition.  If a module does not provide the expected functions, it is
    # simply skipped.
    nebulous_app.register_global_flags(modules)
    nebulous_app.register_shared_flags(modules)
    nebulous_app.register_commands(modules)

    sys.exit(nebulous_app.run())


if __name__ == '__main__':
    main()
