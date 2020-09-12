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

__all__ = ["NetboxDeviceCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


class NetboxDeviceCollection(DeviceCollection):
    name = "netbox"

    async def fetch(self):
        """ exclude devices without a platform or primary-ip address """
        records = await get_client().paginate(
            url="/dcim/devices",
            filters={"exclude": "config_context", "platform__n": "null"},
        )
        self.inventory = [rec for rec in records if rec["primary_ip"]]

    def fingerprint(self, rec: Dict) -> Dict:
        dt = rec["device_type"]
        return {
            "id": rec["id"],
            "sn": rec["serial"],
            "hostname": rec["name"],
            "ipaddr": rec["primary_ip"]["address"].split("/")[0],
            "site": rec["site"]["slug"],
            "os_name": rec["platform"]["slug"],
            "vendor": dt["manufacturer"]["slug"],
            "model": dt["slug"],
        }
