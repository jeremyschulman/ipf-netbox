from typing import Dict

from ipfnbtk.collections.devices import DeviceCollection
from ipfnbtk.sources.netbox.client import NetboxClient


class NetboxDeviceCollection(DeviceCollection):
    name = "netbox"

    def __init__(self):
        super(NetboxDeviceCollection, self).__init__()
        self.client = NetboxClient()
        self.client.timeout = 30

    async def fetch(self):
        """ exclude devices without a platform or primary-ip address """
        records = await self.client.paginate(
            url="/dcim/devices",
            filters={"exclude": "config_context", "platform__n": "null"},
        )
        self.inventory = [rec for rec in records if rec["primary_ip"]]

    def fingerprint(self, rec: Dict) -> Dict:
        return {
            "id": rec["id"],
            "sn": rec["serial"],
            "hostname": rec["name"],
            "ipaddr": rec["primary_ip"]["address"].split("/")[0],
            "site": rec["site"]["slug"],
        }
