from typing import Dict, Tuple, Any

from ipf_netbox.collection import Collection
from ipf_netbox.collections.sites import SiteCollection
from ipf_netbox.netbox.source import NetboxSource


class NetboxSiteCollection(Collection, SiteCollection):
    source_class = NetboxSource

    async def fetch(self):
        nb = self.source.client
        self.inventory.extend(await nb.paginate(url="/dcim/sites"))

    def fingerprint(self, rec: Dict) -> Tuple[Any, Dict]:
        return rec["id"], {"name": rec["slug"]}
