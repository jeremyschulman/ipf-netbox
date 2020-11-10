import asyncio
from typing import Set


from httpx import Response

from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff
from ipf_netbox.tasks.tasktools import with_sources, diff_report_brief
from ipf_netbox.ipfabric.portchans import IPFabricPortChannelCollection
from ipf_netbox.netbox.portchans import NetboxPortChanCollection
from ipf_netbox.igather import iawait

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@with_sources
async def ensure_lags(ipf, nb, **params) -> Set[str]:

    print("\nEnsure Device LAG member interfaces.")

    ipf_col_pc: IPFabricPortChannelCollection = get_collection(  # noqa
        source=ipf, name="portchans"
    )

    nb_col_pc: NetboxPortChanCollection = get_collection(  # noqa
        source=nb, name="portchans"
    )

    print("Fetching from IP Fabric ... ", flush=True, end="")

    if (filters := params.get("filters")) is not None:
        await ipf_col_pc.fetch(filters=filters)

    elif (ipf_device_list := params.get("devices")) is not None:
        # if provided device collection, then use that device list to find the
        # associated port-channels

        print(f"{len(ipf_device_list)} devices ... ", flush=True, end="")

        await iawait(
            (
                ipf_col_pc.fetch(filters=f"hostname = {hostname}")
                for hostname in ipf_device_list
            ),
            limit=100,
        )

    else:
        raise RuntimeError("Request lag parameters missing.")

    ipf_col_pc.make_keys()
    print(f"{len(ipf_col_pc)} items.")

    if not len(ipf_col_pc):
        return set()

    hostname_set = {rec["hostname"] for rec in ipf_col_pc.inventory.values()}

    print("Fetching from Netbox ... ", flush=True, end="")

    await asyncio.gather(
        *(nb_col_pc.fetch(hostname=hostname) for hostname in hostname_set)
    )

    nb_col_pc.make_keys()
    print(f"{len(ipf_col_pc)} items.")

    diff_res = diff(source_from=ipf_col_pc, sync_to=nb_col_pc)
    if not diff_res:
        print("No changes required.")
        return hostname_set

    diff_report_brief(diff_res)

    if params.get("dry_run", False) is True:
        return hostname_set

    tasks = list()
    if diff_res.missing:
        tasks.append(_diff_create(nb_col_pc, diff_res.missing))

    if diff_res.changes:
        tasks.append(_diff_update(nb_col_pc, diff_res.changes))

    if diff_res.extras:
        tasks.append(_diff_extras(nb_col_pc, diff_res.extras))

    await asyncio.gather(*tasks)
    return hostname_set


# -----------------------------------------------------------------------------
#
#                            PRIVATE CODE BEGINS
#
# -----------------------------------------------------------------------------


async def _diff_create(col: NetboxPortChanCollection, missing: dict):
    def _report(item, res: Response):
        _key, _fields = item
        ident = (
            f"{_fields['hostname']}, {_fields['interface']} -> {_fields['portchan']}"
        )
        if res.is_error:
            print(f"CREATE:FAIL: {ident}, {res.text}.")
            return
        print(f"CREATE:OK: {ident}.")

    await col.create_missing(missing=missing, callback=_report)


async def _diff_update(col: NetboxPortChanCollection, changes: dict):
    def _report(_item, res: Response):
        _key, _ch_fields = _item
        _fields = col.inventory[_key]
        ident = (
            f"{_fields['hostname']}, {_fields['interface']} -> {_fields['portchan']}"
        )
        if res.is_error:
            print(f"CHANGE:FAIL: {ident}, {res.text}")
            return
        print(f"CHANGE:OK: {ident}")

    await col.update_changes(changes=changes, callback=_report)


async def _diff_extras(col: NetboxPortChanCollection, extras: dict):
    """
    Extras exist when an interface in Netbox is associated to a LAG, but that
    interface is not associated to the LAG in IPF.  In these cases we need
    to remove the relationship between the NB interface->LAG.
    """

    def _report(_item, res: Response):
        _key, _ch_fields = _item
        _fields = col.inventory[_key]
        ident = (
            f"{_fields['hostname']}, {_fields['interface']} -x {_fields['portchan']}"
        )
        if res.is_error:
            print(f"REMOVE:FAIL: {ident}, {res.text}.")
            return
        print(f"REMOVE:OK: {ident}.")

    await col.remove_extra(extras=extras, callback=_report)
