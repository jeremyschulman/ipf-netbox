from typing import List
import asyncio
from operator import itemgetter

from httpx import Response

from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff
from ipf_netbox.tasks.tasktools import with_sources
from ipf_netbox.ipfabric.interfaces import IPFabricInterfaceCollection
from ipf_netbox.netbox.interfaces import NetboxInterfaceCollection


@with_sources
async def ensure_interfaces(ipf, nb, **params) -> List[str]:
    """
    Ensure Netbox contains devices interfaces found IP Fabric.

    Parameters
    ----------
    ipf: IPFabric Source instance
    nb: Netbox Source instance

    Other Parameters
    ----------------
    dry_run: bool
        Determines dry-run mode

    devices: List[str]
        List of device to use as basis for action

    filters: str
        The IPF device inventory filter expression to use
        as basis for action.

    Returns
    -------
    List[str]
        The list of IPF device hostnames found in the IPF collection.  Can
        be used as a basis for other collection activities.
    """

    print("\nEnsure Device Interfaces.")

    # -------------------------------------------------------------------------
    # Fetch from IP Fabric with the User provided filter expression.
    # -------------------------------------------------------------------------

    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf_col: IPFabricInterfaceCollection = get_collection(  # noqa
        source=ipf, name="interfaces"
    )

    if (filters := params.get("filters")) is not None:
        await ipf_col.fetch(filters=filters)

    elif (ipf_device_list := params.get("devices")) is not None:
        # if provided device collection, then use that device list to find the
        # associated interfaces.

        print(f"{len(ipf_device_list)} devices ... ", flush=True, end="")

        await asyncio.gather(
            *(
                ipf_col.fetch(filters=f"hostname = {hostname}")
                for hostname in ipf_device_list
            )
        )

    else:
        raise RuntimeError("FAIL: no parameters to fetch interfaces")

    ipf_col.make_keys()
    print(f"{len(ipf_col)} items.", flush=True)

    if not len(ipf_col):
        return []

    # create the IPF hostname specific device list for return purposes.
    ipf_device_list = [rec["hostname"] for rec in ipf_col.source_records]

    # -------------------------------------------------------------------------
    # Need to fetch interfaces from Netbox on a per-device basis.
    # -------------------------------------------------------------------------

    print("Fetching from Netbox ... ", flush=True, end="")

    nb_col: NetboxInterfaceCollection = get_collection(  # noqa
        source=nb, name="interfaces"
    )

    col_device_list = {rec["hostname"] for rec in ipf_col.inventory.values()}
    print(f"{len(col_device_list)} devices ... ", flush=True, end="")

    nb.client.timeout = 120
    await asyncio.gather(
        *(nb_col.fetch(hostname=hostname) for hostname in col_device_list)
    )

    nb_col.make_keys()
    print(f"{len(nb_col)} items.", flush=True)

    # -------------------------------------------------------------------------
    # check for differences and process accordingly.
    # -------------------------------------------------------------------------

    diff_res = diff(source_from=ipf_col, sync_to=nb_col)
    if not diff_res:
        print("No changes required.")
        return ipf_device_list

    _diff_report(diff_res)

    if params.get("dry_run", False) is True:
        return ipf_device_list

    tasks = list()
    if diff_res.missing:
        tasks.append(_diff_create(nb_col, diff_res.missing))

    if diff_res.changes:
        tasks.append(_diff_update(nb_col, diff_res.changes))

    await asyncio.gather(*tasks)
    return ipf_device_list


def _diff_report(diff_res):
    print("\nDiff Report")
    print(f"   Missing: count {len(diff_res.missing)}")
    print(f"   Needs Update: count {len(diff_res.changes)}")
    print("\n")


async def _diff_create(nb_col: NetboxInterfaceCollection, missing):
    fields_fn = itemgetter("hostname", "interface")

    def _done(item, _res: Response):
        # _res: Response = task.result()
        _res.raise_for_status()
        _hostname, _if_name = fields_fn(item)
        print(f"CREATE:OK: interface {_hostname}, {_if_name}", flush=True)

    print("CREATE:BEGIN ...")
    await nb_col.create_missing(missing, callback=_done)
    print("CREATE:DONE.")


async def _diff_update(nb_col: NetboxInterfaceCollection, changes):
    fields_fn = itemgetter("hostname", "interface")

    def _done(change, res: Response):
        # res: Response = task.result()
        _hostname, _ifname = fields_fn(change.fingerprint)
        res.raise_for_status()
        print(f"CHANGE:OK: interface {_hostname}, {_ifname}", flush=True)

    print("CHANGE:BEGIN ...")
    await nb_col.update_changes(changes=changes, callback=_done)
    print("CHANGE:DONE.")
