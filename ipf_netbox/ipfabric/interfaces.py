from typing import Dict, Tuple, Any

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

        self.inventory.extend(
            await self.source.client.fetch_table(
                url="/tables/inventory/interfaces",
                columns=["hostname", "intName", "dscr", "siteName"],
                **params,
            )
        )

    def fingerprint(self, rec: Dict) -> Tuple[Any, Dict]:

        return (
            None,
            {
                "interface": expand_interface(rec["intName"]),
                "hostname": normalize_hostname(rec["hostname"]),
                "description": rec["dscr"] or "",
                "site": rec["siteName"],
            },
        )
