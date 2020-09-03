# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict, List
from operator import itemgetter
from functools import partial
import re

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipfnbtk import cache

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["audit"]

# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------

strip_domains = (
    ".mlb.org",
    ".mlb.com",
    ".mlbam.com",
    ".mlbam.mlb.org",
    ".mlbinfra.net",
)

any_domain = "|".join(map(re.escape, strip_domains))
do_strip = partial(re.compile(any_domain).sub, repl="")


def make_keyset(devices, key_fields):
    def normalize_key(host):
        try:
            return do_strip(string=host.lower())
        except:
            breakpoint()
    return {normalize_key(key_fields(rec)): rec for rec in devices}


def actions_for_missing_nb_keys(missing) -> List:
    """
    For any devices in IPF but not in NB, we need to create the Netbox Device
    records given the information from the IPF inventory

    Parameters
    ----------
    missing:
        Missing devices, IPF records

    """
    actions = list()

    for key, ipf_rec in missing.items():
        actions.append(
            {
                "action": "add",
                "target": "netbox",
                "area": "devices",
                "key": key,
                "data": ipf_rec,
            }
        )

    return actions


def actions_for_missing_ipf_keys(missing: Dict) -> List:
    """
    For each device in Netbox but missing in IP Fabric, we need to provide
    the list of managment IP addresses so that we can direct IP Fabric to
    discover these devices.

    Parameters
    ----------
    missing:
        Missing devices, Netbox records
    """
    actions = list()

    for key, nb_rec in missing.items():
        if (ip_addr := nb_rec["primary_ip4"]) is None:
            print(f"WARNING: {nb_rec['name']} missing management IP address, skipping.")
            continue

        actions.append(
            {
                "action": "add",
                "target": "ipfabric",
                "area": "devices",
                "key": key,
                "data": {
                    "site": nb_rec["site"],
                    "ipaddr": ip_addr["address"].split("/")[0],
                },
            }
        )

    return actions


def audit() -> Dict:

    ipf_devices = cache.cache_load("ipfabric", "inventory")
    nb_devices = cache.cache_load("netbox", "inventory")

    ipf_keyset = make_keyset(ipf_devices, itemgetter("hostname"))
    nb_keyset = make_keyset(nb_devices, itemgetter("name"))

    nb_keys = set(nb_keyset)
    ipf_keys = set(ipf_keyset)

    nb_missing_keys = ipf_keys - nb_keys
    ipf_missing_keys = nb_keys - ipf_keys

    nb_actions = actions_for_missing_nb_keys(
        dict(zip(nb_missing_keys, map(ipf_keyset.get, nb_missing_keys)))
    )

    cache.cache_dump(nb_actions, "netbox", "device.actions")

    ipf_actions = actions_for_missing_ipf_keys(
        dict(zip(ipf_missing_keys, map(nb_keyset.get, ipf_missing_keys)))
    )

    cache.cache_dump(ipf_actions, "ipfabric", "device.actions")

    return {"netbox": nb_actions, "ipfabric": ipf_actions}
