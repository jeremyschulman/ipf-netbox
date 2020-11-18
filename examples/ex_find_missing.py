# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import asyncio
import json

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.config import load_default_config_file
from ipf_netbox.collection import get_collection
from ipf_netbox.netbox.devices import NetboxDeviceCollection
from ipf_netbox.ipfabric.devices import IPFabricDeviceCollection
from ipf_netbox.tasks.tasktools import with_sources
from ipf_netbox.diff import diff


@with_sources
async def ensure_devices(ipf, netbox, **params):

    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf_col: IPFabricDeviceCollection = get_collection(  # noqa
        source=ipf, name="devices"
    )

    filters = params["ipf_filters"]

    await ipf_col.fetch(filters=filters)
    ipf_col.make_keys("hostname")

    print(f"{len(ipf_col)} items.", flush=True)

    if not len(ipf_col.source_records):
        print(f"Done. No source_records matching filter:\n\t{filters}")
        return ipf_col

    print("Fetching from Netbox ... ", flush=True, end="")
    nb_col: NetboxDeviceCollection = get_collection(  # noqa
        source=netbox, name="devices"
    )

    await nb_col.fetch(filters=params.get("nb_filters"))

    # now filter the netbox device records to include only those in the "active"
    # or "offline" status since all other records are not in scope for this
    # example use-case.
    # TODO: need to add filtering capability to the netbox fetch() method.

    nb_col.source_records = [
        rec
        for rec in nb_col.source_records
        if (rec["status"]["value"] in ["active", "offline"])
    ]

    print(f"{len(nb_col)} items.", flush=True)
    nb_col.make_keys("hostname")

    diff_res = diff(source_from=nb_col, sync_to=ipf_col)
    if not diff_res.missing:
        print("No missing items in IPF.")
        return

    print(f"IPF missing {len(diff_res.missing)} items that are in NB.")
    with open("missing.json", "w+") as ofile:
        json.dump(diff_res.missing, ofile, indent=3)


def main():
    load_default_config_file()
    asyncio.run(
        ensure_devices(ipf_filters="family != lap", nb_filters=dict(platform__n="null"))
    )
