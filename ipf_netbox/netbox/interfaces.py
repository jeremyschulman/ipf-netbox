# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict, Optional
import asyncio

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import Collector, CollectionCallback
from ipf_netbox.collections.interfaces import InterfaceCollection
from ipf_netbox.netbox.source import NetboxSource, NetboxClient

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["NetboxInterfaceCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


class NetboxInterfaceCollection(Collector, InterfaceCollection):
    source_class = NetboxSource

    async def fetch(self, hostname):
        """ fetch interfaces must be done on a per-device (hostname) basis """

        self.inventory.extend(
            await self.source.client.paginate(
                url="/dcim/interfaces/", filters={"device": hostname}
            )
        )

    def fingerprint(self, rec: Dict) -> Dict:
        return dict(
            hostname=rec["device"]["name"],
            interface=rec["name"],
            description=rec["description"],
        )

    async def create_missing(
        self, missing, callback: Optional[CollectionCallback] = None
    ):
        tasks = dict()
        client: NetboxClient = self.source.client

        callback = callback or (lambda _k, _t: True)

        device_records = await client.fetch_devices(
            hostname_list=(rec["hostname"] for rec in missing.values()), key="name"
        )

        for key, item in missing.items():
            hostname, if_name = key
            if hostname not in device_records:
                print(f"ERROR: device {hostname} missing.")
                continue

            # TODO: set the interface type correctly based on some kind of mapping definition.
            #       for now, use this name-basis for loopback, vlan, port-channel.

            if_type = (
                "virtual" if if_name.lower().startswith(("l", "v", "p")) else "other"
            )

            task = asyncio.create_task(
                client.post(
                    url="/dcim/interfaces/",
                    json=dict(
                        device=device_records[hostname]["id"],
                        name=if_name,
                        description=item["description"],
                        type=if_type,
                    ),
                )
            )
            task.add_done_callback(lambda _t: callback(tasks[_t], _t))
            tasks[task] = key

        await asyncio.gather(*tasks)

    async def update_changes(
        self, changes: Dict, callback: Optional[CollectionCallback] = None
    ):
        # Presently the only field to update is description; so we don't need to put
        # much logic into this post body process.  Might need to in the future.

        tasks = dict()
        client: NetboxClient = self.source.client
        callback = callback or (lambda _k, _t: True)

        for key, item in changes.items():
            if_id = self.inventory_keys[key]["id"]
            task = asyncio.create_task(
                client.patch(
                    url=f"/dcim/interfaces/{if_id}/",
                    json=dict(description=item.fields["description"]),
                )
            )
            tasks[task] = key
            task.add_done_callback(lambda _t: callback(tasks[_t], _t))

        await asyncio.gather(*tasks)
