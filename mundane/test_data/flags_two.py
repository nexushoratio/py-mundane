"""No global flags, yes shared flags, yes commands."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:  # pragma: no cover
    import argparse

    from mundane import app


def mundane_shared_flags(ctx: app.ArgparseApp):
    """Register shared flags."""
    parser = ctx.new_shared_parser('foo')
    if parser:
        parser.add_argument(
            '-x',
            '--xyzzy',
            action='store',
            required=True,
            help='The xyzzy input.')
        parser.add_argument(
            '-k',
            '--keep',
            action=ctx.argparse_api.BooleanOptionalAction,
            help='Keep intermediates.')
    else:
        raise Exception('called again')  # pylint: disable=broad-exception-raised


def mundane_commands(ctx: app.ArgparseApp):
    """Register all module commands."""
    parser = ctx.register_command(ingest_new_material)
    parser.add_argument(
        '-f',
        '--filename',
        action='store',
        required=True,
        help='Filename to ingest.')

    ctx.register_command(process)

    dance_flags = ctx.argparse_api.ArgumentParser(add_help=False)
    dance_args = ('-n', '--now')
    dance_kwargs = {
        'default': False,
        'action': ctx.argparse_api.BooleanOptionalAction,
        'help': 'Now or later. (default: %(default)s)',
    }
    dance_flags.add_argument(*dance_args, **dance_kwargs)
    parser = ctx.register_command(dance, parents=[dance_flags])


def ingest_new_material(args: argparse.Namespace) -> int:
    """Take in new material.

    Read the material and do something useful with it.



    This is a second paragraph that has more details on what is going on in
    this command.  Including long sentences that wrap.
    """
    print('ingesting material from', args.filename)
    return 5


def process(args: 'argparse.Namespace') -> int:
    """Process random data."""
    del args
    return 1


def dance(args: 'argparse.Namespace') -> int:
    """Like no one is watching.
    Second line here.

    Rest of the content.
    """
    if args.now:
        raise AttributeError('issue #18')

    raise RuntimeError('generic exception handling')
