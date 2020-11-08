from importlib import metadata
import os

import click
import httpx
import uvloop

from ipf_netbox.config import load_config_file
from ipf_netbox import consts

VERSION = metadata.version("ipf-netbox")


@click.group()
@click.version_option(VERSION)
@click.option(
    "--config",
    "-C",
    type=click.File(),
    is_eager=True,
    default=lambda: os.environ.get(consts.ENV_CONFIG_FILE, consts.DEFAULT_CONFIG_FILE),
    callback=lambda ctx, param, value: load_config_file(filepath=value),
)
def cli(**kwargs):
    """ IP Fabric - Netbox Utility"""
    pass


@cli.command("test")
def test():
    from code import interact

    interact(local=globals())


def script():
    uvloop.install()

    try:
        cli()
    except httpx.HTTPStatusError as exc:
        print(f"FAIL: HTTP error {exc.response.text}")
