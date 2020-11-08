import click
import asyncio

from ipf_netbox.cli.__main__ import cli
from ipf_netbox.tasks.sites import ensure_sites
from ipf_netbox.tasks.devices import ensure_devices
from ipf_netbox.tasks.ipaddrs import ensure_ipaddrs
from ipf_netbox.tasks.interfaces import ensure_interfaces


@cli.group(name="task")
@click.option("--dry-run", is_flag=True, help="Dry-run mode")
def cli_task(**kwargs):
    """
    Execute a specific task
    """
    pass


# -----------------------------------------------------------------------------
#
#                                 Ensure Sites
#
# -----------------------------------------------------------------------------


@cli_task.command("ensure-sites")
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


@cli_task.command(
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
    "--filter", "filters", help="IPF device inventory filter expression",
)
@click.option(
    "--force-primary-ip",
    is_flag=True,
    help="When IP is already set, update IP if different",
)
@click.pass_context
def cli_ensure_devices(ctx: click.Context, **task_options):
    group_params = ctx.parent.params

    asyncio.run(ensure_devices(params=task_options, group_params=group_params))


# -----------------------------------------------------------------------------
#
#                                 Ensure IP Addresses
#
# -----------------------------------------------------------------------------


@cli_task.command(
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


# -----------------------------------------------------------------------------
#
#                                 Ensure Device Interfaces
#
# -----------------------------------------------------------------------------


@cli_task.command(
    "ensure-interfaces",
    help="""
\b
Ensure Netbox contains Device Interfaces from IP Fabric
\b
--filter <expr> is used to select IP Fabric address records
""",
)
@click.option("--filter", "filters", help="IPF filter expression", required=True)
@click.pass_context
def cli_ensure_interfaces(ctx: click.Context, filters: str):
    group_params = ctx.parent.params

    asyncio.run(ensure_interfaces(**group_params, filters=filters))
