import asyncio
from invoke import task, Context
from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff
from .root import root


@root.add_task
@task(name="ensure-sites")
def ensure_sites(ctx: Context):
    """
    Ensure Netbox contains the sites defined in IP Fabric
    """

    source_ipf = get_source("ipfabric")
    source_netbox = get_source("netbox")

    col_ipf = get_collection(source=source_ipf, name="sites")
    col_netbox = get_collection(source=source_netbox, name="sites")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(col_ipf.catalog(), col_netbox.catalog()))

    diff_res = diff(source_from=col_ipf, sync_to=col_netbox)
    if ctx.config.run.dry:
        print("Show DRY report")
        return

    print("Do something")
    print(diff_res)
