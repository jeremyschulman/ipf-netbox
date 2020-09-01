#!/usr/bin/env python3.8
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

import click
import sys
import os
from operator import itemgetter
from aioipfabric import IPFabricClient
from ipfnbtk.cli.filtering import create_filter
from ipfnbtk.cli.__main__ import cli

# These environment variables must be set to use this script:
ENV_VARS = ["IPF_ADDR", "IPF_USERNAME", "IPF_PASSWORD"]

# These device fields will be stored into the CSV file in this order:
CSV_FIELDNAMES = ["hostname", "siteName", "vendor", "platform", "family", "version"]

DEFAULT_INVENTORY_FILENAME = "inventory.csv"

try:
    ipf_addr, ipf_username, ipf_pw = itemgetter(*ENV_VARS)(os.environ)

except KeyError as exc:
    sys.exit(f"Missing variable {exc.args[0]}")


@cli.command()
@click.option("--limit", multiple=True, help="limit records", is_eager=True)
@click.option("--exclude", multiple=True, help="exclude records", is_eager=True)
@click.option(
    "--ofile", help="output inventory filename", default=DEFAULT_INVENTORY_FILENAME
)
def inventory(ofile, limit, exclude):
    """
    Create an inventory CSV file from IP Fabric device inventory
    """
    ipf = IPFabricClient()
    print("Fetching device inventory from IP Fabirc")
    devices = ipf.devices
    field_names = list(devices[0].keys())
    iter_recs = iter(devices)

    if limit:
        iter_recs = filter(
            create_filter(constraints=limit, field_names=field_names), iter_recs
        )

    if exclude:
        iter_recs = filter(
            create_filter(constraints=exclude, field_names=field_names, include=False),
            iter_recs,
        )

    print(f"Saving inventory CSV to: {ofile}")
    ipf.to_csv(list(iter_recs), ofile, fieldnames=CSV_FIELDNAMES)
    sys.exit(0)


