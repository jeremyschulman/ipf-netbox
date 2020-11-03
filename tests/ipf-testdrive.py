import asyncio
from ipf_netbox.ipfabric import IPFabricDeviceCollection
from ipf_netbox.ipfabric import get_client

loop = asyncio.get_event_loop()
asyncio.set_event_loop(loop)

get_client()

ipf = IPFabricDeviceCollection()
loop.run_until_complete(ipf.fetch())


def exclude_lap(fp):
    return False if fp["os_name"] == "lap" else True


ipf.make_fingerprints(with_filter=exclude_lap)
ipf.make_keys()
