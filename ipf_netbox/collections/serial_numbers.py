# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import List, Dict

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox import cache
from ipf_netbox.normalize_hostname import normalize_hostname

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["audit"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


def audit() -> List[Dict]:
    """
    Audit the IPF serial-numbers against Netbox.  Find any NB device records
    that are either missing a serial-number or have serial-number mismatch.

    Returns
    -------
    List of action records.
    """

    nb_devices = cache.cache_load("netbox", cache.CACHE_DEVICE_INVENTORY)
    ipf_devices = cache.cache_load("ipfabric", cache.CACHE_DEVICE_INVENTORY)

    # first find all netbox records that are missing serial-numbers; these we
    # need to create update action

    nb_no_sn = dict()
    nb_sn = dict()

    for rec in nb_devices:
        hostname = normalize_hostname(rec["name"])
        if rec["serial"]:
            nb_sn[hostname] = rec
        else:
            nb_no_sn[hostname] = rec

    # now find the corresponding IPF records that have the serial-number

    actions = list()

    for rec in ipf_devices:
        actual_sn = rec["sn"]

        if (hostname := normalize_hostname(rec["hostname"])) in nb_no_sn:
            nb_rec = nb_no_sn[hostname]
            actions.append(
                {
                    "action": "add",
                    "source": "netbox",
                    "item": "device",
                    "key": nb_rec["id"],
                    "data": {"name": nb_rec["name"], "serial": actual_sn},
                }
            )

        # check for mismatch serial-numbers
        elif (nb_rec := nb_sn.get(hostname)) and (
            (current := nb_rec["serial"]) != actual_sn
        ):

            actions.append(
                {
                    "action": "update",
                    "source": "netbox",
                    "item": "device",
                    "key": nb_rec["id"],
                    "data": {
                        "name": nb_rec["name"],
                        "serial": actual_sn,
                        "current_serial": current,
                    },
                }
            )

    cache.cache_dump(actions, "netbox", cache.CACHE_SERAILNUMBER_ACTIONS)
    return actions
