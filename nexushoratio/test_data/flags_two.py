"""No global flags."""


def nh_shared_flags(ctx: 'nexushoratio.ArgparserApp'):
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
