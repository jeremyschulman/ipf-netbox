# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Dict, List
from operator import itemgetter

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox import cache
from ipf_netbox.normalize_hostname import normalize_hostname
from .collection import Collection

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["DeviceCollection"]


class DeviceCollection(Collection):
    name = "devices"

    FINGERPRINT_FIELDS = (
        "_ref",
        "sn",
        "hostname",
        "ipaddr",
        "site",
        "os_name",
        "vendor",
        "model",
    )

    KEY_FIELDS = ("sn",)


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


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
                "source": "netbox",
                "item": "device",
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
                "source": "ipfabric",
                "item": "device",
                "key": key,
                "data": {
                    "site": nb_rec["site"],
                    "ipaddr": ip_addr["address"].split("/")[0],
                },
            }
        )

    return actions


def make_keyset(devices, host_field):
    return {normalize_hostname(host_field(rec)): rec for rec in devices}


def audit() -> Dict:

    ipf_devices = cache.cache_load("ipfabric", cache.CACHE_DEVICE_INVENTORY)
    nb_devices = cache.cache_load("netbox", cache.CACHE_DEVICE_INVENTORY)

    ipf_keyset = make_keyset(ipf_devices, itemgetter("hostname"))
    nb_keyset = make_keyset(nb_devices, itemgetter("name"))

    nb_keys = set(nb_keyset)
    ipf_keys = set(ipf_keyset)

    nb_missing_keys = ipf_keys - nb_keys
    ipf_missing_keys = nb_keys - ipf_keys

    nb_actions = actions_for_missing_nb_keys(
        dict(zip(nb_missing_keys, map(ipf_keyset.get, nb_missing_keys)))
    )

    cache.cache_dump(nb_actions, "netbox", cache.CACHE_DEVICE_ACTIONS)
    cache.cache_dump(nb_missing_keys, "netbox", cache.CACHE_DEVICE_MISSING)

    ipf_actions = actions_for_missing_ipf_keys(
        dict(zip(ipf_missing_keys, map(nb_keyset.get, ipf_missing_keys)))
    )

    cache.cache_dump(ipf_actions, "ipfabric", cache.CACHE_DEVICE_ACTIONS)
    cache.cache_dump(ipf_missing_keys, "ipfabric", cache.CACHE_DEVICE_MISSING)

    return {
        "netbox": {"actions": nb_actions, "missing": nb_missing_keys},
        "ipfabric": {"actions": ipf_actions, "missing": ipf_missing_keys},
    }
