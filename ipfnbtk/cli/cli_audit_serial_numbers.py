# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from operator import itemgetter
from collections import defaultdict

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from tabulate import tabulate

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .cli_audit import cli_audit
from ipfnbtk.serial_numbers import audit

# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


@cli_audit.command("serial-numbers")
def cli_audit_serial_numbers():
    """
    Audit IPF serial-numbers against Netbox
    """
    results = audit()
    actions = defaultdict(list)
    for rec in results:
        actions[rec["action"]].append(rec)

    if (
        tabular_data := [
            (rec["data"]["name"], rec["data"]["serial"]) for rec in actions["add"]
        ]
    ) :
        print("\nNetbox: add serial-number to device:\n")

        tabular_data.sort(key=itemgetter(0))

        print(tabulate(headers=["host", "serial-number"], tabular_data=tabular_data))

    if (
        tabular_data := [
            (rec["data"]["name"], rec["data"]["current_serial"], rec["data"]["serial"])
            for rec in actions["update"]
        ]
    ) :
        print("\nNetbox: add serial-number to device:\n")

        tabular_data.sort(key=itemgetter(0))

        print(
            tabulate(
                headers=["host", "NB serial-number", "IPF serial-number"],
                tabular_data=tabular_data,
            )
        )
