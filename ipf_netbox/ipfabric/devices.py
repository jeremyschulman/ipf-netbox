# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import Collection
from ipf_netbox.collections.devices import DeviceCollection
from ipf_netbox.ipfabric.source import IPFabricSource

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPFabricDeviceCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


class IPFabricDeviceCollection(Collection, DeviceCollection):
    source_class = IPFabricSource

    async def fetch(self):
        async with self.source.client as ipf:
            res = await ipf.fetch_devices()

        return res

    def fingerprint(self, rec: Dict) -> Dict:
        return dict(
            sn=rec["sn"],
            hostname=rec["hostname"],
            ipaddr=rec["loginIp"],
            site=rec["siteName"],
            os_name=rec["family"],
            vendor=rec["vendor"],
            model=rec["model"],
        )
