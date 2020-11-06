# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import Collection
from ipf_netbox.collections.interfaces import InterfaceCollection
from ipf_netbox.netbox.source import NetboxSource

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["NetboxInterfaceCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


class NetboxInterfaceCollection(Collection, InterfaceCollection):
    source_class = NetboxSource

    async def fetch(self, hostname):
        """ fetch interfaces must be done on a per-device (hostname) basis """

        return await self.source.client.paginate(
            url="/dcim/interfaces/", filters={"device": hostname}
        )

    def fingerprint(self, rec: Dict) -> Dict:

        return dict(
            hostname=rec["device"]["name"],
            interface=rec["name"],
            description=rec["description"],
        )
