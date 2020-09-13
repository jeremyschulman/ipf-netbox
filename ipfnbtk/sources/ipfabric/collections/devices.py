# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipfnbtk.collections.devices import DeviceCollection
from ..client import get_client

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFabricDeviceCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


class IPFabricDeviceCollection(DeviceCollection):
    source = "ipfabric"

    async def fetch(self):
        res = await get_client().fetch_devices()
        self.inventory = res["data"]

    def fingerprint(self, rec: Dict) -> Dict:
        return dict(
            _id=rec["id"],
            sn=rec["sn"],
            hostname=rec["hostname"],
            ipaddr=rec["loginIp"],
            site=rec["siteName"],
            os_name=rec["family"],
            vendor=rec["vendor"],
            model=rec["platform"],
        )
