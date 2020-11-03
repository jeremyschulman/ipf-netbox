from typing import Dict

from ipf_netbox.collection import Collection
from ipf_netbox.collections.sites import SiteCollection
from ipf_netbox.netbox.source import NetboxSource


class NetboxSiteCollection(Collection, SiteCollection):
    source_class = NetboxSource

    async def fetch(self):

        async with self.source.client_class() as nb:
            return await nb.paginate(url="/dcim/sites")

    def fingerprint(self, rec: Dict) -> Dict:
        return {"name": rec["slug"]}
