import asyncio
import os
import sys
import json
from pathlib import Path

import aiofiles
from tabulate import tabulate

from ipfnbtk.config import load_config_file
from ipfnbtk.normalize_hostname import normalize_hostname
from ipfnbtk.collections.devices import DeviceCollection  # noqa
from ipfnbtk.sources.netbox import NetboxDeviceCollection
from ipfnbtk.sources.ipfabric import IPFabricDeviceCollection
from ipfnbtk.sources.netbox.client import get_client as get_nb
from ipfnbtk.sources.ipfabric.client import get_client as get_ipf
from ipfnbtk.filtering import create_filter
from ipfnbtk.collections import diff


try:
    _CACHEDIR = Path(os.environ["IPFNB_CACHEDIR"])
    assert _CACHEDIR.is_dir(), f"{str(_CACHEDIR)} is not a directory"

except KeyError as exc:
    sys.exit(f"Missing environment variable: {exc.args[0]}")


load_config_file(Path(os.environ['IPFNB_CONFIG']))

loop = asyncio.get_event_loop()
asyncio.set_event_loop(loop)

ipf = get_ipf()
nb = get_nb()

source = NetboxDeviceCollection()
other = IPFabricDeviceCollection()


async def fetch():
    print(f"FETCH: Both Netbox and IP Fabric inventories")
    await asyncio.gather(source.fetch(), other.fetch())

    print(f"SAVE: Both Netbox and IP Fabric inventories")

    async with aiofiles.open(_CACHEDIR.joinpath('netbox.devices.json'), 'w+') as ofile:
        await ofile.write(json.dumps(source.inventory, indent=3))

    async with aiofiles.open(_CACHEDIR.joinpath('ipfabric.devices.json'), 'w+') as ofile:
        await ofile.write(json.dumps(other.inventory, indent=3))


def reload():
    source.inventory = json.load(_CACHEDIR.joinpath('netbox.devices.json').open())
    other.inventory = json.load(_CACHEDIR.joinpath('ipfabric.devices.json').open())


reload()

src_filter_func = create_filter(['status=(active|offline|staged)'], field_names=['status'])
otr_filter_func = create_filter(['os_name=lap'], field_names=['os_name'], include=False)

source.make_fingerprints(with_filter=src_filter_func)
other.make_fingerprints(with_filter=otr_filter_func)
source.make_keys('hostname', with_translate=normalize_hostname)
other.make_keys('hostname', with_translate=normalize_hostname)

missing, changes = diff.diff(source, other, ignore_fields=['os_name', 'hostname'])


missing_sn = [
    (fp, change)
    for fp, change in changes
    if 'sn' in change and fp['sn'] == ''
]

wrong_sn = [
    [fp['hostname'], fp['model'], fp['sn'], change['model'], change['sn']]
    for fp, change in changes
    if 'sn' in change and fp['sn'] != ''
]

print(tabulate(
    headers=['hostname', 'Model', 'SN', 'actual Model', 'actual SN'],
    tabular_data=wrong_sn))
