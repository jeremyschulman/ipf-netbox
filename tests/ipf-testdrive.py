import asyncio
from ipfnbtk.sources.ipfabric import IPFabricDeviceCollection

loop = asyncio.get_event_loop()
asyncio.set_event_loop(loop)

ipf = IPFabricDeviceCollection()
loop.run_until_complete(ipf.fetch())
