# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict

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
        async with self.source.client as api:
            records = await api.paginate(
                url="/dcim/devices/",
                filters={"exclude": "config_context", "platform__n": "null"},
            )

        return [rec for rec in records if rec["primary_ip"]]

    def fingerprint(self, rec: Dict) -> Dict:
        dt = rec["device_type"]

        return dict(
            sn=rec["serial"],
            hostname=rec["name"],
            ipaddr=rec["primary_ip"]["address"].split("/")[0],
            site=rec["site"]["slug"],
            os_name=rec["platform"]["slug"],
            vendor=dt["manufacturer"]["slug"],
            model=dt["slug"],
            status=rec["status"]["value"],
        )
