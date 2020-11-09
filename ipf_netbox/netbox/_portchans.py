# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict, Optional, Tuple
import asyncio
from itertools import chain

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import Collector, CollectionCallback
from ipf_netbox.collections.portchans import PortChannelCollection
from ipf_netbox.netbox.source import NetboxSource, NetboxClient
from ipf_netbox.diff import Changes
from ipf_netbox.igather import igather

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["NetboxPortChanCollection"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------

_INTFS_URL = "/dcim/interfaces/"
_MEMBERS_KEY = "__members__"


class NetboxPortChanCollection(Collector, PortChannelCollection):
    source_class = NetboxSource

    async def fetch(self, hostname, **params):
        """
        fetch interfaces must be done on a per-device (hostname) basis.
        fetch args are Netbox API specific.
        """

        # if (col_ifaces := self.cache.get('interfaces')) is None:
        #     col_ifaces = self.cache['interfaces'] = get_collection(
        #         source=self, name='interfaces'
        #     )

        nb_api: NetboxClient = self.source.client

        nb_filters = params.copy()
        nb_filters["device"] = hostname
        nb_filters["type"] = "lag"

        records = await nb_api.paginate(url=_INTFS_URL, filters=nb_filters)

        # ---------------------------------------------------------------------
        # Get any LAG member interfaces.  Store these members as a dict where
        # key=<if-name>, value=<if-id> so that changes and be made to existing
        # members if necessary.
        # ---------------------------------------------------------------------

        for rec in records:
            res = await nb_api.get(_INTFS_URL, params={"lag_id": rec["id"]})
            members = {rec["name"]: rec["id"] for rec in res.json()["results"]}
            rec[_MEMBERS_KEY] = members

        self.source_records.extend(records)

    async def fetch_keys(self, keys: Dict):
        await asyncio.gather(
            *(
                self.fetch(hostname=rec["hostname"], name=rec["interface"])
                for rec in keys.values()
            )
        )

    def fingerprint(self, rec: Dict) -> Dict:
        return dict(
            hostname=rec["device"]["name"],
            interface=rec["name"],
            members=set(rec[_MEMBERS_KEY].keys()),
        )

    async def update_changes(
        self,
        changes: Dict[Tuple, Changes],
        callback: Optional[CollectionCallback] = None,
    ):
        # the only 'change' is the set of member interfaces.  For members that
        # have been removed, we need to delete the LAG parent ID. For members
        # that have been added, we need to add the LAG parent ID.  Since it is
        # possible for a member interface to "move" we will iterate the deletes
        # and the iterate the adds before calling the patches.  The patch
        # operations are made to the member interface records only.
        #
        # Members are stored as a set():
        #
        #    change.fingerprint['members'] == HAS
        #    change.fields['members'] == SHOULD
        #
        #    SHOULD - HAS = members to add
        #    HAS - SHOULD = members to delete

        api: NetboxClient = self.source.client

        add_if_lag = dict()
        del_if_lag = dict()

        for lag_key, lag_change in changes.items():
            has = lag_change.fingerprint["members"]
            should = lag_change.fields["members"]

            del_if_members = has - should
            add_if_members = should - has

            lag_srec = self.source_record_keys[lag_key]
            dev_id = lag_srec["device"]["id"]
            lag_id = lag_srec["id"]

            del_if_lag.update({(dev_id, if_name): lag_id for if_name in del_if_members})

            add_if_lag.update({(dev_id, if_name): lag_id for if_name in add_if_members})

        # next fetch all affected member interfaces because those need to have
        # some change to their `lag` field.

        all_affected = set(add_if_lag) | set(del_if_lag)

        res = await asyncio.gather(
            *(
                api.get(_INTFS_URL, params=dict(device_id=dev_id, name=if_name))
                for dev_id, if_name in all_affected
            )
        )

        if_recs = list(chain.from_iterable(rec.json()["results"] for rec in res))

        # update the `lag` field to either be cleared or updated to new parent
        # LAG interface

        for if_rec in if_recs:
            if_key = (if_rec["device"]["id"], if_rec["name"])
            if if_key in del_if_lag:
                if_rec["lag"] = None
            if if_key in add_if_lag:
                if_rec["lag"] = add_if_lag[if_key]

        tasks = dict()

        for if_rec in if_recs:
            coro = api.patch(
                url=_INTFS_URL + f"{if_rec['id']}/", json={"lag": if_rec["lag"]}
            )
            tasks[coro] = {
                "hostname": if_rec["device"]["name"],
                "member": if_rec["name"],
            }

        callback = callback or (lambda _k, _t: True)

        async for orig_coro, res in igather(tasks, limit=100):
            item = tasks[orig_coro]
            callback(item, res)
