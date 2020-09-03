# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from operator import itemgetter

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from tabulate import tabulate

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .cli_audit import cli_audit
from ipfnbtk.devices import audit

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["audit"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


@cli_audit.command(name="devices")
def audit_devices():
    """
    Run audit between IPF and Netbox device inventories

    This command will generate reports ....
    """
    results = audit()

    # -------------------------------------------------------------------------
    # Netbox
    # -------------------------------------------------------------------------

    rec_fields = itemgetter("siteName", "loginIp", "vendor", "family", "platform")

    if (
        tabular_data := [
            (rec["key"], *rec_fields(rec["data"]))
            for rec in results["netbox"]["actions"]
        ]
    ) :
        print("\nNetbox Actions: Add/verify devices\n")

        tabular_data.sort(key=itemgetter(1, 0))

        print(
            tabulate(
                headers=["device", "site", "ipaddr", "vendor", "family", "model"],
                tabular_data=tabular_data,
            ),
            "\n",
        )

    # -------------------------------------------------------------------------
    # IP Fabric
    # -------------------------------------------------------------------------

    print("IP Fabric Actions: Discover devices\n")

    if (
        tabular_data := [
            (rec["key"], rec["data"]["site"], rec["data"]["ipaddr"])
            for rec in results["ipfabric"]["actions"]
        ]
    ) :
        tabular_data.sort(key=itemgetter(1, 0))

        print(
            tabulate(headers=["device", "site", "ipaddr"], tabular_data=tabular_data),
            "\n",
        )
        print("IP address list:", ",".join(map(itemgetter(2), tabular_data)), "\n")
