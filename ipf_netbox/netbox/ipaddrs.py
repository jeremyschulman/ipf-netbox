from typing import Dict, Optional
from operator import itemgetter
import asyncio

from ipf_netbox.collection import Collector, CollectionCallback
from ipf_netbox.collections.ipaddrs import IPAddrCollection
from ipf_netbox.netbox.source import NetboxSource, NetboxClient

_IPAM_ADDR_URL = "/ipam/ip-addresses/"


class NetboxIPAddrCollection(Collector, IPAddrCollection):
    source_class = NetboxSource

    async def fetch(self, hostname, **params):
        """ fetch args are Netbox specific API parameters """

        self.source_records.extend(
            await self.source.client.paginate(
                url=_IPAM_ADDR_URL, filters=dict(device=hostname, **params)
            )
        )

    async def fetch_keys(self, keys):
        await asyncio.gather(
            *(
                self.fetch(hostname=rec["hostname"], address=rec["ipaddr"])
                for rec in keys.values()
            )
        )

    def fingerprint(self, rec: Dict) -> Dict:
        if_dat = rec["interface"]
        return {
            "ipaddr": rec["address"],
            "hostname": if_dat["device"]["name"],
            "interface": if_dat["name"],
        }

    async def create_missing(
        self, missing, callback: Optional[CollectionCallback] = None
    ):

        client: NetboxClient = self.source.client

        # for each missing record we will need to fetch the interface record so
        # we can bind the address to it.

        if_key_fn = itemgetter("hostname", "interface")
        if_items = map(if_key_fn, missing.values())
        if_recs = await client.fetch_devices_interfaces(if_items)
        if_lkup = {(rec["device"]["name"], rec["name"]): rec for rec in if_recs}

        api = self.source.client

        def _create_task(key, item):
            if_key = if_key_fn(item)
            if (if_rec := if_lkup.get(if_key)) is None:
                print(
                    "SKIP: ipaddr {}, missing interface: {}, {}.".format(key, *if_key)
                )
                return None

            payload = dict(address=item["ipaddr"], interface=if_rec["id"])

            if if_rec["name"].lower().startswith("loopback"):
                payload["role"] = "loopback"

            return asyncio.create_task(api.post(url=_IPAM_ADDR_URL, json=payload))

        await self.source.update(missing, callback, _create_task)

    async def update_changes(
        self, changes: Dict, callback: Optional[CollectionCallback] = None
    ):
        emsg = f"{self.__class__.__name__}:update not implemented."
        print(emsg)
        # raise NotImplementedError(emsg)
