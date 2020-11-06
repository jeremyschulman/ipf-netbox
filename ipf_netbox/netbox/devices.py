# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict, Tuple, Any

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import Collection
from ipf_netbox.collections.devices import DeviceCollection
from ipf_netbox.netbox.source import NetboxSource

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["NetboxDeviceCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


class NetboxDeviceCollection(Collection, DeviceCollection):
    source_class = NetboxSource

    async def fetch(self, **kwargs):
        """ exclude devices without a platform or primary-ip address """
        api = self.source.client
        self.inventory.extend(
            await api.paginate(
                url="/dcim/devices/", filters={"exclude": "config_context"},
            )
        )

    def fingerprint(self, rec: Dict) -> Tuple[Any, Dict]:
        dt = rec["device_type"]

        try:
            ipaddr = rec["primary_ip"]["address"].split("/")[0]
        except (TypeError, KeyError):
            ipaddr = ""

        try:
            os_name = rec["platform"]["slug"]
        except (TypeError, KeyError):
            os_name = ""

        return (
            rec["id"],
            dict(
                sn=rec["serial"],
                hostname=rec["name"],
                ipaddr=ipaddr,
                site=rec["site"]["slug"],
                os_name=os_name,
                vendor=dt["manufacturer"]["slug"],
                model=dt["slug"],
                status=rec["status"]["value"],
            ),
        )
