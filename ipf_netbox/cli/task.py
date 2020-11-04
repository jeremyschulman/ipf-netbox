import click

from ipf_netbox.cli.__main__ import cli
from ipf_netbox.tasks.sites import ensure_sites
from ipf_netbox.tasks.devices import ensure_devices

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


@cli_tasks.command(
    "ensure-devices",
    help="""
\b
Ensure Netbox has the same Sites as defined in IP Fabric.
\b
--filter <expr> is used to select devices from IP Fabric inventory.
\b
    Examples:
    --filter "siteName = atl"
    --filter 'and(siteName=atl, vendor=cisco)'

""",
)
@click.option(
    "--filter", "filter_", help="IPF filter expression",
)
@click.pass_context
def cli_ensure_devices(ctx: click.Context, filter_: str):
    group_params = ctx.parent.params

    ensure_devices(**group_params, filter_=filter_)
