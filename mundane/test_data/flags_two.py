"""No global flags, yes shared flags, yes commands."""


def nh_shared_flags(ctx: 'mundane.ArgparserApp'):
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


def nh_commands(ctx: 'mundane.ArgparserApp'):
    """Register all module commands."""
    parser = ctx.register_command(ingest_new_material)
    parser.add_argument(
        '-f',
        '--filename',
        action='store',
        required=True,
        help='Filename to ingest.')

    ctx.register_command(process)

    parser = ctx.register_command(dance)
    parser.add_argument(
        '-n',
        '--now',
        default=False,
        action=ctx.argparse_api.BooleanOptionalAction,
        help='Now or later. (default: %(default)s)')


def ingest_new_material(args: 'argparse.Namespace') -> int:
    """Take in new material.

    Read the material and do something useful with it.

    This is a second paragraph that has more details on what is going on in
    this command.  Including long sentences that wrap.
    """
    print('ingest_material got', args)


def process(args: 'argparse.Namespace') -> int:
    """Process random data."""
    print('procssing', args)


def dance(args: 'argparse.Namespace') -> int:
    """Like no one is watching.
    Second line here.

    Rest of the content.
    """
