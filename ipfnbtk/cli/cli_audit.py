from types import MappingProxyType
from operator import itemgetter

import click
from tabulate import tabulate


from ipfnbtk.cli.__main__ import cli

SYSTEM_AREAS = ["devices", "interfaces"]


def audit_devices():
    from ipfnbtk.devices import audit

    results = audit()

    # -------------------------------------------------------------------------
    # Netbox
    # -------------------------------------------------------------------------

    rec_fields = itemgetter("siteName", "loginIp", "vendor", "family", "platform")

    if (
        tabular_data := [
            (rec["key"], *rec_fields(rec["data"])) for rec in results["netbox"]
        ]
    ) :
        print("Netbox Actions: Add devices\n")

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
            for rec in results["ipfabric"]
        ]
    ) :
        tabular_data.sort(key=itemgetter(1, 0))

        print(tabulate(headers=["device", "site", "ipaddr"], tabular_data=tabular_data))

        print("IP address list:", ",".join(map(itemgetter(2), tabular_data)))


def audit_interfaces():
    pass


_SYSTEM_AUDITS = MappingProxyType(
    {"devices": audit_devices, "interfaces": audit_interfaces}
)


@cli.command()
@click.option(
    "--area",
    required=True,
    multiple=True,
    help="area of system to audit",
    type=click.Choice(_SYSTEM_AUDITS),
)
def audit(area):
    """
    Audit systems areas, such as devices, interfaces, ...
    """
    for check_area in SYSTEM_AREAS:
        if check_area in area:
            _SYSTEM_AUDITS[check_area]()
