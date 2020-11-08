# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict, Optional
import asyncio

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import Collector, CollectionCallback
from ipf_netbox.collections.devices import DeviceCollection
from ipf_netbox.netbox.source import NetboxSource, NetboxClient
from ipf_netbox.config import get_config
from ipf_netbox.diff import Changes

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["NetboxDeviceCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------

_DEVICES_URL = "/dcim/devices/"


class NetboxDeviceCollection(Collector, DeviceCollection):
    source_class = NetboxSource

    async def fetch(self, **kwargs):
        """ exclude devices without a platform or primary-ip address """
        self.inventory.extend(
            await self.source.client.paginate(
                url=_DEVICES_URL, filters={"exclude": "config_context"},
            )
        )

    def fingerprint(self, rec: Dict) -> Dict:
        dt = rec["device_type"]

        try:
            ipaddr = rec["primary_ip"]["address"].split("/")[0]
        except (TypeError, KeyError):
            ipaddr = ""

        try:
            os_name = rec["platform"]["slug"]
        except (TypeError, KeyError):
            os_name = ""

        return dict(
            sn=rec["serial"],
            hostname=rec["name"],
            ipaddr=ipaddr,
            site=rec["site"]["slug"],
            os_name=os_name,
            vendor=dt["manufacturer"]["slug"],
            model=dt["slug"],
            status=rec["status"]["value"],
        )

    async def create_missing(
        self, missing: Dict, callback: Optional[CollectionCallback] = None
    ):
        config = get_config()

        nb_api = self.source.client

        device_types, sites, device_role, platforms = await asyncio.gather(
            nb_api.paginate(url="/dcim/device-types/"),
            nb_api.paginate(url="/dcim/sites/"),
            nb_api.paginate(url="/dcim/device-roles/", filters={"slug": "unknown"}),
            nb_api.paginate(url="/dcim/platforms/"),
        )

        device_types = {rec["slug"]: rec["id"] for rec in device_types}
        sites = {rec["slug"]: rec["id"] for rec in sites}
        role_unknwon = device_role[0]["id"]
        platforms = {rec["slug"]: rec["id"] for rec in platforms}

        def _create_task(key, item):  # noqa
            model = item["model"]

            if (dt_slug := config.maps["models"].get(model)) is None:
                print(f"ERROR: no device-type mapping for model {model}, skipping.")
                return None

            if (dt_id := device_types.get(dt_slug)) is None:
                print(f"ERROR: no device-type for slug {dt_slug}, skipping.")
                return None

            if (site_id := sites.get(item["site"])) is None:
                print(f"ERROR: missing site {item['site']}, skipping.")
                return None

            if (pl_id := platforms.get(item["os_name"])) is None:
                print(f"ERROR: missing platform {item['os_name']}, skipping.")
                return None

            return asyncio.create_task(
                nb_api.post(
                    url="/dcim/devices/",
                    json={
                        "name": item["hostname"],
                        "serial": item["sn"],
                        "device_role": role_unknwon,
                        "platform": pl_id,
                        "site": site_id,
                        "device_type": dt_id,
                    },
                )
            )

        await self.source.update(missing, callback, _create_task)

    async def update_changes(
        self, changes: Dict, callback: Optional[CollectionCallback] = None
    ):

        api: NetboxClient = self.source.client

        # ensure that the 'ipaddrs' Collection is in the cache.

        if (cached_ipaddrs := self.cache.get("ipaddrs")) is None:
            # we need to fetch all ipaddrs from Netbox so that they can be processed
            # in the create task function below.

            # ipaddr_list = [
            #     (self.keys[key]['hostname'], item.fields['ipaddr'])
            #     for key, item in changes.items()
            #     if 'ipaddr' in item.fields
            # ]
            #
            # cached_ipaddrs = await self._ensure_ipaddrs(ipaddr_list)

            whoami = self.__class__.__name__
            print(f"SKIP: {whoami}.update_changes requires 'ipaddrs' in cache")
            return

        # TODO: Hacking the cache to remove the pflen because the IP in the device
        #       record does not have that information from IPF.

        kex_lkup = {
            rec["address"].split("/")[0]: rec
            for rec in cached_ipaddrs.inventory_keys.values()
        }

        def _create_task(key, item: Changes):
            """ key is the seriali number """
            patch_payload = {}

            if (ipaddr := item.fields.get("ipaddr")) is not None:

                if (nb_rec := kex_lkup.get(ipaddr)) is None:
                    print(f"SKIP: ipaddr {ipaddr} not in device cache.")
                    return None

                patch_payload["primary_ip4"] = nb_rec["id"]

            if not len(patch_payload):
                return None

            dev_id = self.inventory_keys[key]["id"]

            # Note: no slash between the base URL and the dev_id since the
            #       base url has a slash-suffix

            return asyncio.create_task(
                api.patch(url=f"{_DEVICES_URL}{dev_id}/", json=patch_payload)
            )

        await self.source.update(changes, callback, creator=_create_task)

    # async def _ensure_ipaddrs(self, ipaddr_list):
    #     col_ipaddrs = get_collection(source=self.source, name='ipaddrs')
    #
    #     await asyncio.gather(*(col_ipaddrs.fetch(hostname=hostname, address=ipaddr)
    #                            for hostname, ipaddr, in ipaddr_list))
    #
    #     col_ipaddrs.make_keys()
    #
    #     # if all ipaddrs were found in Netbox, then we can return the collection now.
    #     # otherwise we will need to create
    #     if len(col_ipaddrs) == len(ipaddr_list):
    #         return col_ipaddrs
    #
    #     breakpoint()
    #
    #     return col_ipaddrs
