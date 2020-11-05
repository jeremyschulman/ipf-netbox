import click
import asyncio

from ipf_netbox.cli.__main__ import cli
from ipf_netbox.tasks.sites import ensure_sites
from ipf_netbox.tasks.devices import ensure_devices
from ipf_netbox.tasks.ipaddrs import ensure_ipaddrs


@cli.group(name="tasks")
@click.option("--dry-run", is_flag=True, help="Dry-run mode")
def cli_tasks(**kwargs):
    """
    Execute a specific task
    """
    pass


# -----------------------------------------------------------------------------
#
#                                 Ensure Sites
#
# -----------------------------------------------------------------------------


@cli_tasks.command("ensure-sites")
@click.pass_context
def cli_ensure_sites(ctx: click.Context):
    """ Ensure Netbox has the same Sites as defined in IP Fabric"""

    params = ctx.parent.params
    asyncio.run(ensure_sites(**params))


# -----------------------------------------------------------------------------
#
#                                 Ensure Devices
#
# -----------------------------------------------------------------------------


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

    asyncio.run(ensure_devices(**group_params, filter_=filter_))


# -----------------------------------------------------------------------------
#
#                                 Ensure IP Addresses
#
# -----------------------------------------------------------------------------


@cli_tasks.command(
    "ensure-ipaddrs",
    help="""
\b
Ensure Netbox contains the Managed IP Addresses from IP Fabric
\b
--filter <expr> is used to select IP Fabric address records
""",
)
@click.option(
    "--filter", "filters", help="IPF filter expression",
)
@click.pass_context
def cli_ensure_ipaddrs(ctx: click.Context, filters: str):
    group_params = ctx.parent.params

    asyncio.run(ensure_ipaddrs(**group_params, filters=filters))
