import asyncio

from invoke import task
from tabulate import tabulate
from operator import itemgetter
from httpx import Response

from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff
from ipf_netbox.netbox.source import NetboxClient

from .root import root


@root.add_task
@task(name="ensure-sites")
def ensure_sites(ctx):
    """
    Ensure Netbox contains the sites defined in IP Fabric
    """
    print("Ensure Netbox contains the Sites defined in IP Fabric", flush=True)
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

    loop.run_until_complete(
        _execute_changes(nb=source_netbox.client, diff_res=diff_res)
    )
    loop.run_until_complete(asyncio.gather(source_netbox.client.aclose()))


async def _execute_changes(nb: NetboxClient, diff_res):
    # for each of the sites that do not exist, create one

    def _report(_task: asyncio.Task):
        res: Response = _task.result()
        name = _task.get_name()
        if res.is_error:
            print(f"CREATE site: {name}: FAIL: {res.text}")
            return
        print(f"CREATE site: {name}: OK")

    tasks = [
        asyncio.create_task(
            coro=nb.post(url="/dcim/sites/", json={"name": name, "slug": name}),
            name=name,
        )
        for name in diff_res.missing
    ]

    [_t.add_done_callback(_report) for _t in tasks]

    await asyncio.gather(*tasks, return_exceptions=True)


def _dry_report(source_col, diff_res):

    if not len(diff_res.missing):
        print("No changes required.")
        return

    tab_data = [[key, key not in diff_res.missing] for key in source_col.keys]
    tab_data.sort(key=itemgetter(0))

    print(tabulate(headers=["Site Name", ""], tabular_data=tab_data))
