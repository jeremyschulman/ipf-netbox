# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import asyncio
from operator import itemgetter

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from tabulate import tabulate
from httpx import Response

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff, DiffResults
from ipf_netbox.netbox.devices import NetboxDeviceCollection
from ipf_netbox.ipfabric.devices import IPFabricDeviceCollection
from ipf_netbox.tasks.tasktools import with_sources


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@with_sources
async def ensure_devices(ipf, netbox, **params) -> IPFabricDeviceCollection:
    """
    Ensure Netbox contains devices found IP Fabric.

    Parameters
    ----------
    ipf: IPFabric Source instance
    netbox: Netbox Source instance

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
    IPFabricDeviceCollection:
        The IP Fabric device collection, that can be used by later processes
        that need to cross reference this information.
    """
    print("\nEnsure Devices.")
    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf_col: IPFabricDeviceCollection = get_collection(  # noqa
        source=ipf, name="devices"
    )

    filters = params["filters"]

    await ipf_col.fetch(filters=filters)
    ipf_col.make_keys()

    print(f"{len(ipf_col)} items.", flush=True)

    if not len(ipf_col.source_records):
        print(f"Done. No source_records matching filter:\n\t{filters}")
        return ipf_col

    print("Fetching from Netbox ... ", flush=True, end="")
    netbox_col: NetboxDeviceCollection = get_collection(  # noqa
        source=netbox, name="devices"
    )

    await netbox_col.fetch()
    netbox_col.make_keys()

    print(f"{len(netbox_col)} items.", flush=True)

    diff_res = diff(
        source_from=ipf_col,
        sync_to=netbox_col,
        fields_cmp={
            "model": lambda f: True  # TODO: do not consider model for diff right now
        },
    )

    if diff_res is None:
        print("No changes required.")
        return ipf_col

    _report_proposed_changes(diff_res)

    if params.get("dry_run", False) is True:
        return ipf_col

    updates = list()

    if diff_res.missing:
        updates.append(_execute_create(ipf_col, netbox_col, diff_res.missing))

    if diff_res.changes:
        updates.append(_execute_changes(params, ipf_col, netbox_col, diff_res.changes))

    await asyncio.gather(*updates)

    return ipf_col


def _report_proposed_changes(diff_res: DiffResults):
    if diff_res.missing:
        print("\nNetbox Missing Devices")
        tabular_data = sorted(
            map(
                itemgetter("hostname", "site", "ipaddr", "vendor", "model"),
                diff_res.missing.values(),
            ),
            key=itemgetter(0, 1),
        )

        print(
            tabulate(
                tabular_data=tabular_data,
                headers=["Hostname", "Site", "IP address", "Vendor", "Model"],
            ),
            end="\n\n",
        )

    if diff_res.changes:
        print("\nDifferences:", end="\n")
        for sn, changes in diff_res.changes.items():
            fp = changes.fingerprint
            hostname = fp["hostname"]
            kv_pairs = ", ".join(
                f"{k_}: {fp[k_] or '(empty)'} -> {v_}"
                for k_, v_ in changes.fields.items()
            )
            print(f"Device {hostname}: {kv_pairs}")
        print("\n")


async def _ensure_primary_ipaddrs(
    ipf_col: IPFabricDeviceCollection, nb_col: NetboxDeviceCollection, missing: dict
):

    ipf_col_ipaddrs = get_collection(source=ipf_col.source, name="ipaddrs")
    ipf_col_ifaces = get_collection(source=ipf_col.source, name="interfaces")

    # -------------------------------------------------------------------------
    # we need to fetch all of the IPF ipaddr records so that we can bind the
    # management IP address to the Netbox device record.  We use the **IPF**
    # collection as the basis for the missing records so that the filter values
    # match.  This is done to avoid any mapping changes that happended via the
    # collection intake process.  This code is a bit of 'leaky-abstration',
    # so TODO: cleanup.
    # -------------------------------------------------------------------------

    await asyncio.gather(
        *(
            ipf_col_ipaddrs.fetch(
                filters=f"and(hostname = {_item['hostname']}, ip = '{_item['loginIp']}')"
            )
            for _item in [ipf_col.source_record_keys[key] for key in missing.keys()]
        )
    )

    ipf_col_ipaddrs.make_keys()

    # -------------------------------------------------------------------------
    # now we need to gather the IPF interface records so we have any _fields that
    # need to be stored into Netbox (e.g. description)
    # -------------------------------------------------------------------------

    await asyncio.gather(
        *(
            ipf_col_ifaces.fetch(
                filters=f"and(hostname = {_item['hostname']}, intName = {_item['intName']})"
            )
            for _item in ipf_col_ipaddrs.source_record_keys.values()
        )
    )

    ipf_col_ifaces.make_keys()

    # -------------------------------------------------------------------------
    # At this point we have the IPF collections for the needed 'interfaces' and
    # 'ipaddrs'.  We need to ensure these same entities exist in the Netbox
    # collections.  We will first attempt to find all the existing records in
    # Netbox using the `fetch_keys` method.
    # -------------------------------------------------------------------------

    nb_col_ifaces = get_collection(source=nb_col.source, name="interfaces")
    nb_col_ipaddrs = get_collection(source=nb_col.source, name="ipaddrs")

    await nb_col_ifaces.fetch_keys(keys=ipf_col_ifaces.inventory)
    await nb_col_ipaddrs.fetch_keys(keys=ipf_col_ipaddrs.inventory)

    nb_col_ipaddrs.make_keys()
    nb_col_ifaces.make_keys()

    diff_ifaces = diff(source_from=ipf_col_ifaces, sync_to=nb_col_ifaces)
    diff_ipaddrs = diff(source_from=ipf_col_ipaddrs, sync_to=nb_col_ipaddrs)

    def _report_iface(item, _res: Response):
        _key, _fields = item
        hname, iname = _fields["hostname"], _fields["interface"]
        if _res.is_error:
            print(f"CREATE:FAIL: interface {hname}, {iname}: {_res.text}")
            return

        print(f"CREATE:OK: interface {hname}, {iname}.")
        nb_col_ifaces.source_records.append(_res.json())

    def _report_ipaddr(item, _res: Response):
        _key, _fields = item
        hname, iname, ipaddr = (
            _fields["hostname"],
            _fields["interface"],
            _fields["ipaddr"],
        )
        ident = f"ipaddr {hname}, {iname}, {ipaddr}"

        if _res.is_error:
            print(f"CREATE:FAIL: {ident}: {_res.text}")
            return

        nb_col_ipaddrs.source_records.append(_res.json())
        print(f"CREATE:OK: {ident}.")

    if diff_ifaces:
        await nb_col_ifaces.create_missing(
            missing=diff_ifaces.missing, callback=_report_iface
        )

    if diff_ipaddrs:
        await nb_col_ipaddrs.create_missing(
            missing=diff_ipaddrs.missing, callback=_report_ipaddr
        )

    nb_col.make_keys()
    nb_col_ifaces.make_keys()
    nb_col_ipaddrs.make_keys()

    # TODO: Note that I am passing the cached collections of interfaces and ipaddress
    #       To the device collection to avoid duplicate lookups for record
    #       indexes. Will give this approach some more thought.

    nb_col.cache["interfaces"] = nb_col_ifaces
    nb_col.cache["ipaddrs"] = nb_col_ipaddrs


async def _execute_create(
    ipf_col: IPFabricDeviceCollection, nb_col: NetboxDeviceCollection, missing: dict
):

    # -------------------------------------------------------------------------
    # Now create each of the device records.  Once the device records are
    # created, then go back and add the primary interface and ipaddress values
    # using the other collections.
    # -------------------------------------------------------------------------

    def _report_device(update, _res: Response):
        key, item = update
        if _res.is_error:
            print(f"FAIL: create device {item['hostname']}: {_res.text}")
            return

        print(f"CREATE:OK: device {item['hostname']} ... creating primary IP ... ")
        nb_col.source_records.append(_res.json())

    await nb_col.create_missing(missing=missing, callback=_report_device)
    await _ensure_primary_ipaddrs(ipf_col=ipf_col, nb_col=nb_col, missing=missing)

    # -------------------------------------------------------------------------
    # for each of the missing device records perform a "change request" on the
    # 'ipaddr' field. so that the primary IP will be assigned.
    # -------------------------------------------------------------------------

    changes = {
        key: {"ipaddr": ipf_col.inventory[key]["ipaddr"]} for key in missing.keys()
    }

    def _report_primary(item, _res):  # noqa
        key, fields = item
        rec = nb_col.inventory[key]
        ident = f"device {rec['hostname']} assigned primary-ip4"
        if _res.is_error:
            print(f"CREATE:FAIL: {ident}: {_res.text}")
            return

        print(f"CREATE:OK: {ident}.")

    await nb_col.update_changes(changes, callback=_report_primary)


async def _execute_changes(
    params: dict,
    ipf_col: IPFabricDeviceCollection,
    nb_col: NetboxDeviceCollection,
    changes,
):
    print("\nExaminging changes ... ", flush=True)

    def _report(change, res: Response):
        ch_key, ch_fields = change
        ch_rec = nb_col.inventory[ch_key]
        ident = f"device {ch_rec['hostname']}"
        print(
            f"CHANGE:FAIL: {ident}, {res.text}"
            if res.is_error
            else f"CHANGE:OK: {ident}"
        )

    actual_changes = dict()
    missing_pri_ip = dict()

    for key, key_change in changes.items():
        rec = nb_col.inventory[key]
        if (ipaddr := key_change.pop("ipaddr", None)) is not None:
            if any(
                (
                    rec["ipaddr"] == "",
                    (ipaddr and (params["force_primary_ip"] is True)),
                )
            ):
                key_change["ipaddr"] = ipaddr
                missing_pri_ip[key] = key_change

        if len(key_change):
            actual_changes[key] = key_change

    if missing_pri_ip:
        await _ensure_primary_ipaddrs(
            ipf_col=ipf_col, nb_col=nb_col, missing=missing_pri_ip
        )

    if not actual_changes:
        print("No required changes.")
        return

    print("Processing changes ... ")
    await nb_col.update_changes(changes, callback=_report)
    print("Done.\n")
