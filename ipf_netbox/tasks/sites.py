# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import asyncio

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import Response

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import get_collection
from ipf_netbox.diff import diff
from ipf_netbox.tasks.tasktools import with_sources
from ipf_netbox.diff import DiffResults

from ipf_netbox.netbox.sites import NetboxSiteCollection
from ipf_netbox.ipfabric.sites import IPFabricSiteCollection


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@with_sources
async def ensure_sites(ipf, nb, dry_run):
    """
    Ensure Netbox contains the sites defined in IP Fabric
    """
    print("Ensure Netbox contains the Sites defined in IP Fabric")
    print("Fetching from IP Fabric and Netbox ... ")

    ipf_col_sites: IPFabricSiteCollection = get_collection(  # noqa
        source=ipf, name="sites"
    )

    nb_col_sites: NetboxSiteCollection = get_collection(source=nb, name="sites")  # noqa

    await asyncio.gather(ipf_col_sites.fetch(), nb_col_sites.fetch())

    ipf_col_sites.make_keys()
    nb_col_sites.make_keys()

    print(f"IP Fabric {len(ipf_col_sites)} items.")
    print(f"Netbox {len(nb_col_sites)} items.")

    diff_res = diff(source_from=ipf_col_sites, sync_to=nb_col_sites)

    if diff_res is None:
        print("No changes required.")
        return

    _diff_report(diff_res=diff_res)
    if dry_run:
        return

    if diff_res.missing:
        await _create_missing(nb_col_sites, diff_res.missing)

    if diff_res.changes:
        await _update_changes(nb_col_sites, diff_res.changes)


async def _create_missing(nb_col: NetboxSiteCollection, missing: dict):
    def _report(item, res: Response):
        ident = f"site {item['name']}"
        if res.is_error:
            print(f"CREATE {ident}: FAIL: {res.text}")
            return
        print(f"CREATE {ident}: OK")

    print("CREATE:BEGIN ...")
    await nb_col.create_missing(missing, callback=_report)
    print("CREATE:DONE.")


async def _update_changes(nb_col: NetboxSiteCollection, changes: dict):
    pass


def _diff_report(diff_res: DiffResults):
    print("\nDiff Report")
    print(f"   Missing: count {len(diff_res.missing)}")
    print(f"   Needs Update: count {len(diff_res.changes)}")
    print("\n")
