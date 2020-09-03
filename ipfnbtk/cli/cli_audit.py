
from ipfnbtk.cli.__main__ import cli


@cli.group(name='audit')
def cli_audit():
    """
    Audit systems areas, such as devices, interfaces, ...
    """
    pass
