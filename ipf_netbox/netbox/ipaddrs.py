from typing import Dict, Tuple, Any

from ipf_netbox.collection import Collection
from ipf_netbox.collections.ipaddrs import IPAddrCollection
from ipf_netbox.netbox.source import NetboxSource


class NetboxIPAddrCollection(Collection, IPAddrCollection):
    source_class = NetboxSource

    async def fetch(self, hostname, **params):
        api = self.source.client
        self.inventory.extend(
            await api.paginate(url="/ipam/ip-addresses/", filters={"device": hostname})
        )

    def fingerprint(self, rec: Dict) -> Tuple[Any, Dict]:
        return (
            rec["id"],
            {
                "ipaddr": rec["address"],
                "hostname": rec["device"],
                "interface": rec["interface"],
            },
        )
