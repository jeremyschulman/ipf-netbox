# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict

from aioipfabric.filters import parse_filter

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

    async def fetch(self, **fetch_args):
        filters = (
            {} if "filters" not in fetch_args else parse_filter(fetch_args["filters"])
        )

        async with self.source.client as ipf:
            res = await ipf.fetch_devices(filters=filters)

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
