from importlib import metadata
import os

import click

from ipf_netbox.config import load_config_file
from ipf_netbox import consts


@click.group()
@click.version_option(metadata.version("ipfnbtk"))
@click.option(
    "--config",
    "-C",
    type=click.File(),
    is_eager=True,
    default=lambda: os.environ.get(consts.ENV_CONFIG_FILE, consts.DEFAULT_CONFIG_FILE),
    callback=lambda ctx, param, value: load_config_file(filepath=value),
)
def cli(**kwargs):
    """ IP Fabric - Netbox Toolkit CLI"""
    pass
