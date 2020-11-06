from typing import Dict, Tuple, Any

from ipf_netbox.collection import Collection
from ipf_netbox.collections.sites import SiteCollection
from ipf_netbox.ipfabric.source import IPFabricSource


class IPFabricSiteCollection(Collection, SiteCollection):
    name = "sites"
    source_class = IPFabricSource

    async def fetch(self):
        ipf = self.source.client
        self.inventory.extend(
            await ipf.fetch_table(url="tables/inventory/sites", columns=["siteName"])
        )

    def fingerprint(self, rec: Dict) -> Tuple[Any, Dict]:
        return None, {"name": rec["siteName"]}
