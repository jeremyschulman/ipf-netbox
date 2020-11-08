import asyncio
from operator import itemgetter

from httpx import Response

from ipf_netbox.collection import get_collection, Collector
from ipf_netbox.diff import diff
from ipf_netbox.tasks.tasktools import with_sources


@with_sources
async def ensure_interfaces(ipf, nb, dry_run, filters):
    print("Ensure Netbox contains device interfaces from IP Fabric")

    # -------------------------------------------------------------------------
    # Fetch from IP Fabric with the User provided filter expression.
    # -------------------------------------------------------------------------

    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf_col = get_collection(source=ipf, name="interfaces")
    nb_col = get_collection(source=nb, name="interfaces")

    await ipf_col.fetch(filters=filters)
    ipf_col.make_keys()

    print(f"{len(ipf_col)} items.", flush=True)

    if not len(ipf_col):
        return

    # -------------------------------------------------------------------------
    # Need to fetch interfaces from Netbox on a per-device basis.
    # -------------------------------------------------------------------------

    print("Fetching from Netbox ... ", flush=True, end="")

    device_list = {rec["hostname"] for rec in ipf_col.inventory.values()}
    print(f"{len(device_list)} devices ... ", flush=True, end="")

    nb.client.timeout = 120
    await asyncio.gather(*(nb_col.fetch(hostname=hostname) for hostname in device_list))

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

    await asyncio.gather(*tasks)


def _diff_report(diff_res):
    print("\nDiff Report")
    print(f"   Missing: count {len(diff_res.missing)}")
    print(f"   Needs Update: count {len(diff_res.changes)}")
    print("\n")


async def _diff_create(nb_col, missing):
    fields_fn = itemgetter("hostname", "interface")

    def _done(item, task):
        _res: Response = task.result()
        _res.raise_for_status()
        _hostname, _if_name = fields_fn(item)
        print(f"CREATE:OK: interface {_hostname}, {_if_name}", flush=True)

    await nb_col.create_missing(missing, callback=_done)


async def _diff_update(nb_col: Collector, changes):
    fields_fn = itemgetter("hostname", "interface")

    def _done(change, task):
        res: Response = task.result()
        _hostname, _ifname = fields_fn(change.fingerprint)
        res.raise_for_status()
        print(f"CHANGE:OK: interface {_hostname}, {_ifname}", flush=True)

    await nb_col.update_changes(changes=changes, callback=_done)
