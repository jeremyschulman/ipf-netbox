from typing import Dict, Optional

from ipf_netbox.collection import Collector, CollectionCallback
from ipf_netbox.collections.sites import SiteCollection
from ipf_netbox.netbox.source import NetboxSource, NetboxClient


class NetboxSiteCollection(Collector, SiteCollection):
    source_class = NetboxSource

    async def fetch(self):
        self.source_records.extend(await self.source.client.paginate(url="/dcim/sites"))

    def fingerprint(self, rec: Dict) -> Dict:
        return {"name": rec["slug"]}

    async def create_missing(
        self, missing: Dict, callback: Optional[CollectionCallback] = None
    ):
        api: NetboxClient = self.source.client

        def _creator(key, item):  # noqa
            name = key
            return api.post(
                url="/dcim/sites/", json={"name": name, "slug": api.slugify(name)}
            )

        await self.source.update(updates=missing, callback=callback, creator=_creator)
