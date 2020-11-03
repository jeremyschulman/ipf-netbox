import os
from operator import itemgetter

from ipf_netbox.sources import Source
from aioipfabric.client import IPFabricClient

NAME = "ipfabric"

__all__ = ["IPFabricSource"]


def _init_check():
    ipf_env = IPFabricClient.ENV
    try:
        itemgetter(ipf_env.addr, ipf_env.username, ipf_env.password)(os.environ)

    except KeyError as exc:
        raise RuntimeError(f"Missing environment variable: {exc.args[0]}")


_init_check()


class IPFabricSource(Source):
    name = NAME
    client_class = IPFabricClient
