from typing import Dict
import os
from operator import itemgetter

from aioipfabric.client import IPFabricClient
from ipfnbtk.collections.devices import DeviceCollection


class IPFabricDeviceCollection(DeviceCollection):
    def __init__(self):
        ipf_env = IPFabricClient.ENV
        try:
            itemgetter(ipf_env.addr, ipf_env.username, ipf_env.password)(os.environ)
        except KeyError as exc:
            raise RuntimeError(f"Missing environment variable: {exc.args[0]}")

        super(IPFabricDeviceCollection, self).__init__(name="ipfabric")
        self.client = IPFabricClient()

    async def fetch(self):
        res = await self.client.fetch_devices()
        self.inventory = res["data"]

    def fingerprint(self, rec: Dict) -> Dict:
        return dict(
            id=rec["id"],
            sn=rec["sn"],
            hostname=rec["hostname"],
            ipaddr=rec["loginIp"],
            site=rec["siteName"],
        )
