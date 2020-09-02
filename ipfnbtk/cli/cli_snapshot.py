#  Copyright 2020 Jeremy Schulman
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import sys
import os
from operator import itemgetter
from pathlib import Path
import json

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import click
from aioipfabric import IPFabricClient

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipfnbtk.cli.filtering import create_filter
from ipfnbtk.netbox import NetboxClient
from ipfnbtk.cli.__main__ import cli

# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------

# Snapshot Sources
SOURCE_LIST = ["ipfabric", "netbox"]

# These environment variables must be set to use this script:
ENV_VARS = ["IPF_ADDR", "IPF_USERNAME", "IPF_PASSWORD"]

# These device fields will be stored into the CSV file in this order:
IPF_FIELDNAMES = ["hostname", "siteName", "vendor", "platform", "family", "version"]
NB_FIELDNAMES = ['platform', 'name', 'site', 'status', 'role']


try:
    ipf_addr, ipf_username, ipf_pw = itemgetter(*ENV_VARS)(os.environ)
    nb_addr, nb_token = itemgetter(*NetboxClient.ENV_VARS)(os.environ)

except KeyError as exc:
    sys.exit(f"Missing environment variable: {exc.args[0]}")


def filter_snapshot(devices, fieldnames, limit, exclude):
    iter_recs = iter(devices)

    if limit:
        iter_recs = filter(
            create_filter(constraints=limit, field_names=fieldnames), iter_recs
        )

    if exclude:
        iter_recs = filter(
            create_filter(constraints=exclude, field_names=fieldnames, include=False),
            iter_recs,
        )

    return iter_recs


def save_snapshot(iter_recs, filename):
    ofile = Path(os.environ["IPFNB_CACHEDIR"]).joinpath(filename)
    print(f"IP FABRIC: Saving inventory JSON to: {ofile.absolute()}")
    json.dump(list(iter_recs), ofile.open("w+"), indent=3)


def snapshot_ipfabric(limit, exclude):
    ipf = IPFabricClient()
    print("IP FABRIC: Fetching device inventory")

    devices = ipf.devices
    fieldnames = IPF_FIELDNAMES

    iter_recs = filter_snapshot(devices, fieldnames, limit, exclude)
    save_snapshot(iter_recs, "ipf.inventory.json")


def snapshot_netbox(limit, exclude):
    nb = NetboxClient()

    print("NETBOX: Fetching device inventory")

    devices = nb.devices
    fieldnames = NB_FIELDNAMES

    # going to 'hack' the device records so that the values we want to filter on
    # are first level key=value.

    def transmutate(_dev):
        _dev["platform"] = _dev["platform"]["slug"]
        _dev["role"] = _dev["device_role"]["slug"]
        _dev["site"] = _dev["site"]["slug"]
        _dev["status"] = _dev["status"]["value"]

    for dev in devices:
        transmutate(dev)

    iter_recs = iter(devices)
    iter_recs = filter_snapshot(iter_recs, fieldnames, limit, exclude)
    save_snapshot(iter_recs, "nb.inventory.json")


@cli.command()
@click.option("--limit", multiple=True, help="limit records", is_eager=True)
@click.option("--exclude", multiple=True, help="exclude records", is_eager=True)
@click.option(
    "--source",
    required=True,
    multiple=True,
    help="Source system(s)",
    type=click.Choice(SOURCE_LIST),
)
def snapshot(source, **kwargs):
    """
    Create an inventory snapshot file from IP Fabric device inventory
    """
    if "ipfabric" in source:
        snapshot_ipfabric(**kwargs)

    if "netbox" in source:
        snapshot_netbox(**kwargs)
