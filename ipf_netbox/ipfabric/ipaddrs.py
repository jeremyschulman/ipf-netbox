from typing import Dict

from aioipfabric.filters import parse_filter

from ipf_netbox.collection import Collector
from ipf_netbox.collections.ipaddrs import IPAddrCollection
from ipf_netbox.ipfabric.source import IPFabricSource
from ipf_netbox.mappings import normalize_hostname, expand_interface


class IPFabricIPAddrCollection(Collector, IPAddrCollection):
    source_class = IPFabricSource

    async def fetch(self, **params):

        if (filters := params.get("filters")) is not None:
            params["filters"] = parse_filter(filters)

        self.source_records.extend(
            await self.source.client.fetch_table(
                url="tables/addressing/managed-devs",
                columns=["hostname", "intName", "siteName", "ip", "net"],
                **params,
            )
        )

    def fingerprint(self, rec: Dict) -> Dict:
        try:
            pflen = rec["net"].split("/")[-1]
        except AttributeError:
            pflen = "32"

        return {
            "ipaddr": f"{rec['ip']}/{pflen}",
            "interface": expand_interface(rec["intName"]),
            "hostname": normalize_hostname(rec["hostname"]),
            "site": rec["siteName"],
        }
