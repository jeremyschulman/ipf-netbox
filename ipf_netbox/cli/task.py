import click

from ipf_netbox.cli.__main__ import cli
from ipf_netbox.tasks.sites import ensure_sites


# @cli.command(name="task", context_settings=dict(ignore_unknown_options=True))
# @click.argument("invoke_args", nargs=-1, type=click.UNPROCESSED)
# def cli_task(invoke_args):
#     """
#     Execute task
#     """
#
#     runner.run(invoke_args)


@cli.group(name="tasks")
@click.option("--dry-run", is_flag=True, help="Dry-run mode")
def cli_tasks(**kwargs):
    """
    Execute a specific task
    """
    pass


@cli_tasks.command("ensure-sites")
@click.pass_context
def cli_ensure_sites(ctx: click.Context):
    """ Ensure Netbox has the same Sites as defined in IP Fabric"""

    params = ctx.parent.params
    ensure_sites(**params)
