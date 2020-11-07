from typing import Dict

from ipf_netbox.collection import Collector
from ipf_netbox.collections.sites import SiteCollection
from ipf_netbox.netbox.source import NetboxSource


class NetboxSiteCollection(Collector, SiteCollection):
    source_class = NetboxSource

    async def fetch(self):
        self.inventory.extend(await self.source.client.paginate(url="/dcim/sites"))

    def fingerprint(self, rec: Dict) -> Dict:
        return {"name": rec["slug"]}
