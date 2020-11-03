import asyncio

from invoke import task
from tabulate import tabulate
from operator import itemgetter

from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff
from .root import root


@root.add_task
@task(name="ensure-sites")
def ensure_sites(ctx):
    """
    Ensure Netbox contains the sites defined in IP Fabric
    """
    print("Fetching source data, please wait ... ", flush=True, end="")
    source_ipf = get_source("ipfabric")
    source_netbox = get_source("netbox")

    col_ipf = get_collection(source=source_ipf, name="sites")
    col_netbox = get_collection(source=source_netbox, name="sites")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(col_ipf.catalog(), col_netbox.catalog()))
    print("OK")

    diff_res = diff(source_from=col_ipf, sync_to=col_netbox)
    if ctx.config.run.dry:
        _dry_report(source_col=col_ipf, diff_res=diff_res)
        return

    print("Do something")
    print(col_ipf, diff_res)


def _dry_report(source_col, diff_res):

    tab_data = [[key, key not in diff_res.missing] for key in source_col.keys]
    tab_data.sort(key=itemgetter(0))

    print(tabulate(headers=["Site Name", "Exists"], tabular_data=tab_data))
