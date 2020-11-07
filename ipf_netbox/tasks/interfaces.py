import asyncio

from httpx import Response

from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection, Collector

from ipf_netbox.diff import diff


async def ensure_interfaces(dry_run, filters):
    print("Ensure Netbox contains device interfaces from IP Fabric")

    # -------------------------------------------------------------------------
    # Fetch from IP Fabric with the User provided filter expression.
    # -------------------------------------------------------------------------

    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf_col = get_collection(source=get_source("ipfabric"), name="interfaces")
    nb_col = get_collection(source=get_source("netbox"), name="interfaces")

    async with ipf_col.source.client:
        await ipf_col.fetch(filters=filters)
        ipf_col.make_keys()

    print(f"{len(ipf_col)} items.", flush=True)

    if not len(ipf_col):
        return

    # -------------------------------------------------------------------------
    # Need to fetch interfaces from Netbox on a per-device basis.
    # -------------------------------------------------------------------------

    print("Fetching from Netbox ... ", flush=True, end="")

    device_list = {rec["hostname"] for rec in ipf_col.keys.values()}
    print(f"{len(device_list)} devices ... ", flush=True, end="")

    async with nb_col.source.client as api:
        api.timeout = 120
        await asyncio.gather(
            *(nb_col.fetch(hostname=hostname) for hostname in device_list)
        )

    nb_col.make_keys()
    print(f"{len(nb_col)} items.", flush=True)

    # -------------------------------------------------------------------------
    # check for differences and process accordingly.
    # -------------------------------------------------------------------------

    diff_res = diff(source_from=ipf_col, sync_to=nb_col)
    if not diff_res:
        print("Done, no differences.")
        return

    _diff_report(diff_res)

    if dry_run:
        return

    tasks = list()
    if diff_res.missing:
        tasks.append(_diff_create(nb_col, diff_res.missing))

    if diff_res.changes:
        tasks.append(_diff_update(nb_col, diff_res.changes))

    async with nb_col.source.client:
        await asyncio.gather(*tasks)


def _diff_report(diff_res):
    print("\nDiff Report")
    print(f"   Missing: count {len(diff_res.missing)}")
    print(f"   Needs Update: count {len(diff_res.changes)}")
    print("\n")


async def _diff_create(nb_col, missing):
    def _done(key, _task):
        _res: Response = _task.result()
        _res.raise_for_status()
        _hostname, _if_name = key
        print(f"CREATE:OK: interface {_hostname}, {_if_name}", flush=True)

    await nb_col.create_missing(missing, callback=_done)


async def _diff_update(nb_col: Collector, changes):
    def _done(_key, _task):
        res: Response = _task.result()
        _hostname, _ifname = _key
        res.raise_for_status()
        print(f"UPDATE:OK: interface {_hostname}, {_ifname}", flush=True)

    await nb_col.update_changes(changes=changes, callback=_done)
