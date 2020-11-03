import click

from ipf_netbox.cli.__main__ import cli
from ipf_netbox.tasks import runner


@cli.command(name="task", context_settings=dict(ignore_unknown_options=True))
@click.argument("invoke_args", nargs=-1, type=click.UNPROCESSED)
def cli_task(invoke_args):
    """
    Execute task
    """

    runner.run(invoke_args)
