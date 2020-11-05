from typing import Dict

from ipf_netbox.collection import Collection
from ipf_netbox.collections.ipaddrs import IPAddrCollection
from ipf_netbox.netbox.source import NetboxSource


class NetboxIPAddrCollection(Collection, IPAddrCollection):
    source_class = NetboxSource

    async def fetch(self, hostname, **params):

        async with self.source.client_class() as nb:
            return await nb.paginate(
                url="/ipam/ip-addresses/", filters={"device": hostname}
            )

    def fingerprint(self, rec: Dict) -> Dict:
        return {
            "ipaddr": rec["address"],
            "hostname": rec["device"],
            "interface": rec["interface"],
        }
