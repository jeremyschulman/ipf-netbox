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


@with_sources
async def ensure_devices(ipf, netbox, **params) -> IPFabricDeviceCollection:

    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf_col: IPFabricDeviceCollection = get_collection(  # noqa
        source=ipf, name="devices"
    )

    filters = params["filters"]

    await ipf_col.fetch(filters=filters)
    ipf_col.make_keys()

    print(f"{len(ipf_col)} items.", flush=True)

    if not len(ipf_col.source_records):
        print(f"Done. No source_records matching filter:\n\t{filters}")
        return ipf_col

    print("Fetching from Netbox ... ", flush=True, end="")
    nb_col: NetboxDeviceCollection = get_collection(  # noqa
        source=netbox, name="devices"
    )

    await nb_col.fetch()

    # now filter the netbox device records to include only those in the "active"
    # or "offline" status since all other records are not in scope for this
    # example use-case.
    # TODO: need to add filtering capability to the netbox fetch() method.

    nb_col.source_records = [
        rec
        for rec in nb_col.source_records
        if rec["status"]["value"] in ["active", "offline"]
    ]

    print(f"{len(nb_col)} items.", flush=True)
    nb_col.make_keys()

    with open("netbox-devices.json", "w+") as ofile:
        json.dump(list(nb_col.inventory.values()), ofile, indent=3)

    with open("ipfabric-devices.json", "w+") as ofile:
        json.dump(list(ipf_col.inventory.values()), ofile, indent=3)


def main():
    load_default_config_file()
    asyncio.run(ensure_devices(filters="family != lap"))
