import asyncio
import os
import sys
import json
from pathlib import Path
import csv
from typing import Dict

import aiofiles
from tabulate import tabulate

from ipf_netbox.config import load_config_file
from ipf_netbox.normalize_hostname import normalize_hostname
from ipf_netbox.collections.devices import DeviceCollection  # noqa
from ipf_netbox.netbox import NetboxDeviceCollection
from ipf_netbox.ipfabric import IPFabricDeviceCollection
from ipf_netbox.netbox import get_client as get_nb
from ipf_netbox.ipfabric import get_client as get_ipf
from ipf_netbox.filtering import create_filter
from ipf_netbox.collections import diff


try:
    _CACHEDIR = Path(os.environ["IPFNB_CACHEDIR"])
    assert _CACHEDIR.is_dir(), f"{str(_CACHEDIR)} is not a directory"

except KeyError as exc:
    sys.exit(f"Missing environment variable: {exc.args[0]}")


load_config_file(Path(os.environ["IPFNB_CONFIG"]))


class CiscoSntcCsvDeviceCollection(DeviceCollection):
    source = "cisco-sntc-csv"

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    async def fetch(self):
        self.inventory = list(csv.DictReader(open(self.filename)))

    def fingerprint(self, rec: Dict) -> Dict:
        return dict(
            hostname=rec["Hostname"],
            sn=rec["Serial Number"],
            model=rec["Product ID"],
            os_name=rec["SW Type"],
            vendor="cisco",
            ipaddr=rec["IP Address"],
        )


loop = asyncio.get_event_loop()
asyncio.set_event_loop(loop)

ipf = get_ipf()
nb = get_nb()

source = NetboxDeviceCollection()
other = IPFabricDeviceCollection()

# other = CiscoSntcCsvDeviceCollection(Path("~/tmp/Cisco-SNTC.csv").expanduser())


async def fetch():
    print(f"FETCH: {source.source} and {other.source} inventories")

    await asyncio.gather(source.fetch(), other.fetch())

    print("SAVE: Both Netbox and IP Fabric inventories")

    async with aiofiles.open(
        _CACHEDIR.joinpath(f"{source.source}.devices.json"), "w+"
    ) as ofile:
        await ofile.write(json.dumps(source.inventory, indent=3))

    async with aiofiles.open(
        _CACHEDIR.joinpath(f"{other.source}.devices.json"), "w+"
    ) as ofile:
        await ofile.write(json.dumps(other.inventory, indent=3))


def reload():
    source.inventory = json.load(
        _CACHEDIR.joinpath(f"{source.source}.devices.json").open()
    )
    other.inventory = json.load(
        _CACHEDIR.joinpath(f"{other.source}.devices.json").open()
    )


#    other.inventory = json.load(_CACHEDIR.joinpath("ipfabric.devices.json").open())


def run():

    reload()

    src_filter_func = create_filter(
        ["status=(active|offline|staged|decommissioning)"], field_names=["status"]
    )

    otr_filter_func = create_filter(
        ["os_name=lap"], field_names=["os_name"], include=False
    )
    # otr_filter_func = None

    source.make_fingerprints(with_filter=src_filter_func)
    other.make_fingerprints(with_filter=otr_filter_func)

    # def tr_hostname(val):
    #     return normalize_hostname(val).replace('/', '-')

    source.make_keys("hostname", with_translate=normalize_hostname)
    other.make_keys("hostname", with_translate=normalize_hostname)

    source.make_keys("sn")
    other.make_keys("sn")

    def sn_cmp(val):
        return val if not val.endswith("_1") else val.partition("_1")[0]

    comparitors = {
        "sn": sn_cmp,
        # "model": str.upper,
        # "os_name": lambda f: f.replace("-", ""),
    }

    missing, changes = diff.diff(source, other, fields_cmp=comparitors)

    missing_sn = [
        (fp, change) for fp, change in changes if "sn" in change and fp["sn"] == ""
    ]

    wrong_sn = [
        [
            fp["_id"],
            fp["hostname"],
            fp["os_name"],
            fp["model"],
            change.get("model") or fp["model"],
            fp["sn"],
            change["sn"],
        ]
        for fp, change in changes
        if "sn" in change and fp["sn"] != ""
    ]

    # wrong_model = [
    #     [fp["hostname"], fp["os_name"], fp["model"], change["model"]]
    #     for fp, change in changes
    #     if "model" in change
    # ]

    return missing_sn, wrong_sn


def print_wrong_sn(changes):
    data = [
        [fp["hostname"], fp["os_name"], fp["model"], fp["sn"], fp_c["sn"]]
        for fp, fp_c in changes
        if "sn" in fp_c
    ]
    print(
        tabulate(
            headers=["hostname", "OS", "Model", "SN", "diff SN"], tabular_data=data,
        )
    )


def print_wrong_model(changes):
    data = [
        [fp["hostname"], fp["os_name"], fp["model"], fp_c["model"]]
        for fp, fp_c in changes
        if "model" in fp_c
    ]
    print(
        tabulate(
            headers=["hostname", "OS", "Model", "actual Model"], tabular_data=data,
        )
    )


def task_update_sn(dev_id, sn):
    return nb.patch(f"/dcim/devices/{dev_id}/", json={"serial": sn})


async def fix_all(missing_sn):
    for fp, changes in missing_sn:
        dev_id = fp["_id"]
        print(f"Updating {fp['hostname']} ({dev_id}) to {changes['sn']}")
        res = await task_update_sn(dev_id=dev_id, sn=changes["sn"])
        print(res)
