from typing import Dict

from ipf_netbox.collections.collection import Collection
from ipf_netbox.collections.sites import SiteCollection
from ipf_netbox.sources.ipfabric.source import IPFabricSource


class IPFabricSiteCollection(Collection, SiteCollection):
    name = "sites"
    source_class = IPFabricSource

    async def fetch(self):
        async with self.source.client as ipf:
            return await ipf.fetch_table(
                url="tables/inventory/sites", columns=["siteName"]
            )

    def fingerprint(self, rec: Dict) -> Dict:
        return {"name": rec["siteName"]}
