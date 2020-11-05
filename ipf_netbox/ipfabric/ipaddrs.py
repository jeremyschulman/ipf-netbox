from typing import Dict

from aioipfabric.filters import parse_filter

from ipf_netbox.collection import Collection
from ipf_netbox.collections.ipaddrs import IPAddrCollection
from ipf_netbox.ipfabric.source import IPFabricSource


class IPFabricIPAddrCollection(Collection, IPAddrCollection):
    source_class = IPFabricSource

    async def fetch(self, **params):

        if (filters := params.get("filters")) is not None:
            params["filters"] = parse_filter(filters)

        async with self.source.client as ipf:
            return await ipf.fetch_table(
                url="tables/addressing/managed-devs",
                columns=["hostname", "intName", "siteName", "ip", "net"],
                filters=params["filters"],
            )

    def fingerprint(self, rec: Dict) -> Dict:
        pflen = rec["net"].split("/")[-1]

        return {
            "ipaddr": f"{rec['ip']}/{pflen}",
            "interface": rec["intName"],
            "hostname": rec["hostname"],
            "site": rec["siteName"],
        }
