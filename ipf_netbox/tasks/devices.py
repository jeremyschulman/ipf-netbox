import asyncio
from operator import itemgetter

from tabulate import tabulate

from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff, DiffResults


def ensure_devices(dry_run, filter_):
    """
    Ensure Netbox contains devices found IP Fabric in given Site
    """
    print("Ensure Netbox contains devices found IP Fabric in given Site")
    print("Fetching inventory from IP Fabric ... ", flush=True, end="")

    ipf = get_source("ipfabric")
    ipf_col = get_collection(source=ipf, name="devices")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ipf_col.catalog(with_fetchargs=dict(filters=filter_)))

    print("OK", flush=True)

    if not len(ipf_col.inventory):
        print(f"Done. No inventory matching filter:\n\t{filter_}")
        return

    print("Fetching inventory from Netbox ... ", flush=True, end="")
    netbox = get_source("netbox")
    netbox_col = get_collection(source=netbox, name="devices")
    loop.run_until_complete(netbox_col.catalog())
    print("OK", flush=True)

    diff_res = diff(source_from=ipf_col, sync_to=netbox_col)

    if diff_res is None:
        print("Done.  No changes required.")
        return

    if diff_res:
        _report_proposed_changes(diff_res)
        return

    _execute_changes()


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
            )
        )

    if diff_res.changes:
        pass


def _execute_changes():
    pass
