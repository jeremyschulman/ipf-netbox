import asyncio

from httpx import Response

from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection

from ipf_netbox.diff import diff  # , DiffResults


async def ensure_interfaces(dry_run, filters):
    print("Ensure Netbox contains device interfaces from IP Fabric")

    # -------------------------------------------------------------------------
    # Fetch from IP Fabric with the User provided filter expression.
    # -------------------------------------------------------------------------

    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf_col = get_collection(source=get_source("ipfabric"), name="interfaces")
    nb_col = get_collection(source=get_source("netbox"), name="interfaces")

    async with ipf_col.source.client:
        await ipf_col.fetch(filters=filters)
        ipf_col.make_keys()

    print(f"OK.  {len(ipf_col)} items.", flush=True)

    if not len(ipf_col):
        return

    # -------------------------------------------------------------------------
    # Need to fetch interfaces from Netbox on a per-device basis.
    # -------------------------------------------------------------------------

    print("Fetching from Netbox ... ", flush=True, end="")

    device_list = {rec["hostname"] for rec in ipf_col.keys.values()}
    async with nb_col.source.client:
        await asyncio.gather(
            *(nb_col.fetch(hostname=hostname) for hostname in device_list)
        )

    nb_col.make_keys()
    print(f"OK.  {len(nb_col)} items.", flush=True)

    # -------------------------------------------------------------------------
    # check for differences and process accordingly.
    # -------------------------------------------------------------------------

    diff_res = diff(source_from=ipf_col, sync_to=nb_col)
    if not diff_res:
        print("Done.  no differences.")
        return

    _diff_report(diff_res)

    if dry_run:
        return

    tasks = list()
    if diff_res.missing:
        tasks.append(_diff_create(ipf_col, nb_col, diff_res.missing))

    if diff_res.changes:
        tasks.append(_diff_update(ipf_col, nb_col, diff_res.changes))

    async with nb_col.source.client:
        await asyncio.gather(*tasks)


def _diff_report(diff_res):
    print("\nDiff Report")
    print(f"   Missing: count {len(diff_res.missing)}")
    print(f"   Needs Update: count {len(diff_res.changes)}")
    print("\n")


async def fetch_devices(api, device_list, key="name") -> dict:
    records = dict()

    for next_done in asyncio.as_completed(
        [api.get("/dcim/devices/", params=dict(name=device)) for device in device_list]
    ):
        res = await next_done
        res.raise_for_status()
        rec = res.json()["results"][0]
        records[rec[key]] = rec

    return records


async def _diff_create(ipf_col, nb_col, missing):

    api = nb_col.source.client

    # we need the netbox device records so that we have the device ID to
    # associate with the interface create body.

    device_records = await fetch_devices(
        api, device_list={rec["hostname"] for rec in missing.values()}
    )

    tasks = dict()

    def _done(_task):
        _res: Response = _task.result()
        _res.raise_for_status()
        _hostname, _if_name = tasks[_task]
        print(f"OK. create interface {_hostname}, {_if_name}")

    for key, item in missing.items():
        hostname, if_name = key
        task = asyncio.create_task(
            api.post(
                "/dcim/interfaces/",
                json=dict(
                    device=device_records[hostname]["id"],
                    name=if_name,
                    description=item["description"],
                    # TODO: set the interface type correctly based on some kind of mapping definition.
                    type="other",
                ),
            )
        )
        task.add_done_callback(_done)
        tasks[task] = key

    await asyncio.gather(*tasks)


async def _diff_update(ipf_col, nb_col, changes):
    tasks = dict()

    def _done(_task):
        res: Response = _task.result()
        _hostname, _ifname = tasks[_task]
        res.raise_for_status()
        print(f"OK. update interface {_hostname}, {_ifname}")

    # Presently the only field to update is description; so we don't need to put
    # much logic into this post body process.  Might need to in the future.

    for key, item in changes.items():
        nb_if_id = nb_col.uids[key]
        task = asyncio.create_task(
            nb_col.source.client.patch(
                url=f"/dcim/interfaces/{nb_if_id}/",
                json={"description": item.fields["description"]},
            )
        )
        tasks[task] = key
        task.add_done_callback(_done)

    await asyncio.gather(*tasks)
