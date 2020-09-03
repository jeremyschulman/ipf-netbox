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
from types import MappingProxyType

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import click
from aioipfabric import IPFabricClient

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipfnbtk.cli.filtering import create_filter
from ipfnbtk.netbox.client import NetboxClient

from ipfnbtk import cache
from ipfnbtk.config_models import ConfigModel
from ipfnbtk.cli.cli_snapshot import cli_snapshot

# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------

# These environment variables must be set to use this script:
IPF_ENV_VARS = ["IPF_ADDR", "IPF_USERNAME", "IPF_PASSWORD"]

# These device fields will be stored into the CSV file in this order:
IPF_FIELDNAMES = ["hostname", "siteName", "vendor", "platform", "family", "version"]
NB_FIELDNAMES = ["platform", "name", "site", "status", "role"]


try:
    ipf_addr, ipf_username, ipf_pw = itemgetter(*IPF_ENV_VARS)(os.environ)
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


def snapshot_ipfabric(limit, exclude):
    ipf = IPFabricClient()
    print("IP FABRIC: Fetching device inventory")

    devices = ipf.devices
    fieldnames = IPF_FIELDNAMES

    iter_recs = filter_snapshot(devices, fieldnames, limit, exclude)
    cache.cache_dump(list(iter_recs), "ipfabric", cache.CACHE_DEVICE_INVENTORY)


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
    cache.cache_dump(list(iter_recs), "netbox", cache.CACHE_DEVICE_INVENTORY)


SOURCE_SNAPSHOT = MappingProxyType(
    {"netbox": snapshot_netbox, "ipfabric": snapshot_ipfabric}
)


@cli_snapshot.command(name="devices")
@click.option("--limit", multiple=True, help="limit records", is_eager=True)
@click.option("--exclude", multiple=True, help="exclude records", is_eager=True)
@click.option(
    "--source",
    multiple=True,
    help="Source system(s)",
    type=click.Choice(SOURCE_SNAPSHOT),
    default=list(SOURCE_SNAPSHOT),
)
@click.pass_context
def cli_devices(ctx, source, limit, exclude, **_kwargs):
    """
    Create an inventory snapshot file from IP Fabric device inventory
    """
    config: ConfigModel = ctx.find_root().params["config"]

    for source_name in source:
        source_cfg = config.sources[source_name]
        source_kwargs = {
            "limit": limit or source_cfg.limit,
            "exclude": exclude or source_cfg.exclude,
        }
        SOURCE_SNAPSHOT[source_name](**source_kwargs)
