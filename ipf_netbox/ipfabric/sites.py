from typing import Dict

from ipf_netbox.collection import Collector
from ipf_netbox.collections.sites import SiteCollection
from ipf_netbox.ipfabric.source import IPFabricSource


class IPFabricSiteCollection(Collector, SiteCollection):
    name = "sites"
    source_class = IPFabricSource

    async def fetch(self):
        ipf = self.source.client
        self.inventory.extend(
            await ipf.fetch_table(url="tables/inventory/sites", columns=["siteName"])
        )

    def fingerprint(self, rec: Dict) -> Dict:
        return {"name": rec["siteName"]}
