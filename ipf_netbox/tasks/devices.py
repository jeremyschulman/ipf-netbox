import asyncio
from operator import itemgetter

from tabulate import tabulate

from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff, DiffResults
from ipf_netbox.config import get_config


async def ensure_devices(dry_run, filter_):
    """
    Ensure Netbox contains devices found IP Fabric in given Site
    """
    print("Ensure Netbox contains devices found IP Fabric in given Site")
    print("Fetching inventory from IP Fabric ... ", flush=True, end="")

    ipf = get_source("ipfabric")
    ipf_col = get_collection(source=ipf, name="devices")

    await ipf_col.catalog(with_fetchargs=dict(filters=filter_))

    print("OK", flush=True)

    if not len(ipf_col.inventory):
        print(f"Done. No inventory matching filter:\n\t{filter_}")
        return

    print("Fetching inventory from Netbox ... ", flush=True, end="")
    netbox = get_source("netbox")
    netbox_col = get_collection(source=netbox, name="devices")
    await netbox_col.catalog()
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


async def _execute_create(ipf_col, nb_col, missing):
    config = get_config()

    nb_api = nb_col.source.client

    async with nb_api:
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

    tasks = list()

    def _report(_task):
        _res = _task.result()
        name = _task.get_name()

        if _res.is_error:
            print(f"FAIL: create device {name}: {_res.text}")
            return

        print(f"OK: device {name} created.")

    for sn, device_fp in missing.items():
        model = device_fp["model"]

        if (dt_slug := config.maps["models"].get(model)) is None:
            print(f"ERROR: no device-type mapping for model {model}, skipping.")
            continue

        if (dt_id := device_types.get(dt_slug)) is None:
            print(f"ERROR: no device-type for slug {dt_slug}, skipping.")
            continue

        if (site_id := sites.get(device_fp["site"])) is None:
            print(f"ERROR: missing site {device_fp['site']}, skipping.")
            continue

        if (pl_id := platforms.get(device_fp["os_name"])) is None:
            print(f"ERROR: missing platform {device_fp['os_name']}, skipping.")
            continue

        task = asyncio.create_task(
            nb_api.post(
                url="/dcim/devices/",
                json={
                    "name": device_fp["hostname"],
                    "serial": device_fp["sn"],
                    "device_role": role_unknwon,
                    "platform": pl_id,
                    "site": site_id,
                    "device_type": dt_id,
                },
            ),
            name=device_fp["hostname"],
        )

        task.add_done_callback(_report)
        tasks.append(task)

    async with nb_api:
        nb_api.timeout = 60
        await asyncio.gather(*tasks)


async def _execute_changes(ipf_col, nb_col, changes):
    print("\nPROCESS DEVICE CHANGES: WORK IN PROGRESS\n\n")
