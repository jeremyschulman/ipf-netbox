import asyncio
from operator import itemgetter

from tabulate import tabulate
from httpx import Response

from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff, DiffResults, Changes

from ipf_netbox.netbox.devices import NetboxDeviceCollection
from ipf_netbox.ipfabric.devices import IPFabricDeviceCollection


async def ensure_devices(dry_run, filter_):
    """
    Ensure Netbox contains devices found IP Fabric in given Site
    """
    print("Ensure Netbox contains devices")
    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf = get_source("ipfabric")
    ipf_col: IPFabricDeviceCollection = get_collection(  # noqa
        source=ipf, name="devices"
    )

    async with ipf.client:
        await ipf_col.fetch(filters=filter_)
        ipf_col.make_keys()

    print("OK", flush=True)

    if not len(ipf_col.inventory):
        print(f"Done. No inventory matching filter:\n\t{filter_}")
        return

    print("Fetching inventory from Netbox ... ", flush=True, end="")
    netbox = get_source("netbox")
    netbox_col: NetboxDeviceCollection = get_collection(  # noqa
        source=netbox, name="devices"
    )

    async with netbox.client:
        await netbox_col.fetch()
        netbox_col.make_keys()

    print("OK", flush=True)

    diff_res = diff(
        source_from=ipf_col,
        sync_to=netbox_col,
        fields_cmp={
            "model": lambda f: True  # do not consider model for diff right now
        },
    )

    if diff_res is None:
        print("Done.  No changes required.")
        return

    _report_proposed_changes(diff_res)

    if dry_run:
        return

    updates = list()

    if diff_res.missing:
        updates.append(_execute_create(ipf_col, netbox_col, diff_res.missing))

    if diff_res.changes:
        updates.append(_execute_changes(ipf_col, netbox_col, diff_res.changes))

    async with netbox_col.source.client, ipf_col.source.client as nb:
        nb.timeout = 60
        await asyncio.gather(*updates)


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
            end="\n",
        )

    if diff_res.changes:
        print("\nNetbox Device Updates Identified", end="\n\n")
        for sn, changes in diff_res.changes.items():
            fp = changes.fingerprint
            hostname = fp["hostname"]
            kv_pairs = ", ".join(
                f"{k_}: {fp[k_] or '(empty)'} -> {v_}"
                for k_, v_ in changes.fields.items()
            )
            print(f"Device {hostname}: {kv_pairs}")


async def _ensure_primary_ipaddrs(
    ipf_col: IPFabricDeviceCollection, nb_col: NetboxDeviceCollection, missing
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
            for _item in [ipf_col.inventory_keys[key] for key in missing.keys()]
        )
    )

    ipf_col_ipaddrs.make_keys()

    # -------------------------------------------------------------------------
    # now we need to gather the IPF interface records so we have any fields that
    # need to be stored into Netbox (e.g. description)
    # -------------------------------------------------------------------------

    await asyncio.gather(
        *(
            ipf_col_ifaces.fetch(
                filters=f"and(hostname = {_item['hostname']}, intName = {_item['intName']})"
            )
            for _item in ipf_col_ipaddrs.inventory_keys.values()
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

    await nb_col_ifaces.fetch_keys(keys=ipf_col_ifaces.keys)
    await nb_col_ipaddrs.fetch_keys(keys=ipf_col_ipaddrs.keys)

    nb_col_ipaddrs.make_keys()
    nb_col_ifaces.make_keys()

    diff_ifaces = diff(source_from=ipf_col_ifaces, sync_to=nb_col_ifaces)
    diff_ipaddrs = diff(source_from=ipf_col_ipaddrs, sync_to=nb_col_ipaddrs)

    def _report_iface(item, _task):
        _res = _task.result()
        hname, iname = item["hostname"], item["interface"]
        if _res.is_error:
            print(f"CREATE:FAIL: interface {hname}, {iname}: {_res.text}")
            return

        print(f"CREATE:OK: interface {hname}, {iname}.")
        nb_col_ifaces.inventory.append(_res.json())

    def _report_ipaddr(item, _task):
        _res = _task.result()
        hname, iname, ipaddr = item["hostname"], item["interface"], item["ipaddr"]
        ident = f"ipaddr {hname}, {iname}, {ipaddr}"

        if _res.is_error:
            print(f"CREATE:FAIL: {ident}: {_res.text}")
            return

        nb_col_ipaddrs.inventory.append(_res.json())
        print(f"CREATE:OK: ipaddr {ident}.")

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
    ipf_col: IPFabricDeviceCollection, nb_col: NetboxDeviceCollection, missing
):

    # -------------------------------------------------------------------------
    # Now create each of the device records.  Once the device records are
    # created, then go back and add the primary interface and ipaddress values
    # using the other collections.
    # -------------------------------------------------------------------------

    def _report_device(item, _task):
        _res = _task.result()
        if _res.is_error:
            print(f"FAIL: create device {item['hostname']}: {_res.text}")
            return

        print(f"CREATE:OK: device {item['hostname']} ... creating primary IP ... ")
        nb_col.inventory.append(_res.json())

    await nb_col.create_missing(missing=missing, callback=_report_device)
    await _ensure_primary_ipaddrs(ipf_col=ipf_col, nb_col=nb_col, missing=missing)

    # -------------------------------------------------------------------------
    # for each of the missing device records perform a "change request" on the
    # 'ipaddr' field. so that the primary IP will be assigned.
    # -------------------------------------------------------------------------

    changes = {
        key: Changes(fingerprint={}, fields={"ipaddr": ipf_col.keys[key]["ipaddr"]})
        for key in missing.keys()
    }

    def _report_primary(item, _task):
        _res = _task.result()
        ident = "device primary-ip4"
        if _res.is_error:
            print(f"CREATE:FAIL: {ident}: {_res.text}")
            return

        print(f"CREATE:OK: {ident}.")

    await nb_col.update_changes(changes, callback=_report_primary)


async def _execute_changes(
    ipf_col: IPFabricDeviceCollection, nb_col: NetboxDeviceCollection, changes
):
    def _report(item: Changes, _task):
        res: Response = _task.result()
        ident = f"device {item.fingerprint['hostname']}"
        print(
            f"CHANGE:FAIL: {ident}, {res.text}"
            if res.is_error
            else f"CHANGE:OK: {ident}"
        )

    missing_ipaddrs = {
        key: change.fields
        for key, change in changes.items()
        if "ipaddr" in change.fields
    }

    if missing_ipaddrs:
        await _ensure_primary_ipaddrs(
            ipf_col=ipf_col, nb_col=nb_col, missing=missing_ipaddrs
        )

    await nb_col.update_changes(changes, callback=_report)
