from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection

# from ipf_netbox.diff import diff, DiffResults
# from ipf_netbox.config import get_config


async def ensure_ipaddrs(dry_run, filters):
    print("Ensure Netbox contains IP addresses from IP Fabric")
    print("Fetching from IP Fabric ... ", flush=True, end="")

    ipf = get_source("ipfabric")
    ipf_col = get_collection(source=ipf, name="ipaddrs")

    await ipf_col.catalog(with_fetchargs=dict(filters=filters))

    print("OK", flush=True)

    if not len(ipf_col.inventory):
        print(f"Done. No inventory matching filter:\n\t{filters}")
        return
