from typing import Dict

from ipf_netbox.collection import Collector
from ipf_netbox.collections.ipaddrs import IPAddrCollection
from ipf_netbox.netbox.source import NetboxSource


class NetboxIPAddrCollection(Collector, IPAddrCollection):
    source_class = NetboxSource

    async def fetch(self, hostname, **params):
        api = self.source.client
        self.inventory.extend(
            await api.paginate(url="/ipam/ip-addresses/", filters={"device": hostname})
        )

    def fingerprint(self, rec: Dict) -> Dict:
        return {
            "ipaddr": rec["address"],
            "hostname": rec["device"],
            "interface": rec["interface"],
        }
