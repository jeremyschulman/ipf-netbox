import asyncio
from itertools import chain

from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection

from ipf_netbox.diff import diff  # , DiffResults


async def ensure_interfaces(dry_run, filters):
    print("Ensure Netbox contains device interfaces from IP Fabric")
    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf_col = get_collection(source=get_source("ipfabric"), name="interfaces")
    nb_col = get_collection(source=get_source("netbox"), name="interfaces")

    async with ipf_col.source.client:
        await ipf_col.catalog(with_fetchargs=dict(filters=filters))

    print(f"OK.  {len(ipf_col)} items.", flush=True)

    if not len(ipf_col):
        return

    # -------------------------------------------------------------------------
    # need to fetch interfaces from Netbox on a per-device basis.
    # -------------------------------------------------------------------------

    print("Fetching from Netbox ... ", flush=True, end="")

    device_list = {fp["hostname"] for fp in ipf_col.fingerprints}
    async with nb_col.source.client:
        nb_inventory = await asyncio.gather(
            *(nb_col.fetch(hostname=hostname) for hostname in device_list)
        )

    nb_col.inventory = list(chain.from_iterable(nb_inventory))
    nb_col.make_fingerprints()
    nb_col.make_keys()

    # -------------------------------------------------------------------------
    # check for differences and process accordingly.
    # -------------------------------------------------------------------------

    diff_res = diff(source_from=ipf_col, sync_to=nb_col)

    _report(diff_res)
    if dry_run:
        return

    tasks = list()
    if diff_res.missing:
        tasks.append(_create(ipf_col, nb_col, diff_res.missing))

    if diff_res.changes:
        tasks.append(_update(ipf_col, nb_col, diff_res.changes))

    await asyncio.gather(*tasks)


def _report(diff_res):
    print("\nReport")
    print(f"   MISSING: count {len(diff_res.missing)}")
    print(f"   UPDATE: count {len(diff_res.changes)}")
    print("\n")


async def _create(ipf_col, nb_col, missing):
    pass


async def _update(ipf_col, nb_col, changes):
    pass
