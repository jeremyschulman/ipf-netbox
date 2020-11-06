from typing import Dict

from aioipfabric.filters import parse_filter

from ipf_netbox.collection import Collection
from ipf_netbox.collections.interfaces import InterfaceCollection
from ipf_netbox.ipfabric.source import IPFabricSource

from ipf_netbox.mappings import expand_interface, normalize_hostname


class IPFabricInterfaceCollection(Collection, InterfaceCollection):
    source_class = IPFabricSource

    async def fetch(self, **params):

        if (filters := params.get("filters")) is not None:
            params["filters"] = parse_filter(filters)

        return await self.source.client.fetch_table(
            url="/tables/inventory/interfaces",
            columns=["hostname", "intName", "dscr", "siteName"],
            **params,
        )

    def fingerprint(self, rec: Dict) -> Dict:

        return {
            "interface": expand_interface(rec["intName"]),
            "hostname": normalize_hostname(rec["hostname"]),
            "description": rec["dscr"],
            "site": rec["siteName"],
        }
