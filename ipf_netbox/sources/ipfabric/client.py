import os
from operator import itemgetter
from functools import lru_cache

from aioipfabric.client import IPFabricClient


@lru_cache()
def get_client():
    ipf_env = IPFabricClient.ENV
    try:
        itemgetter(ipf_env.addr, ipf_env.username, ipf_env.password)(os.environ)

    except KeyError as exc:
        raise RuntimeError(f"Missing environment variable: {exc.args[0]}")

    return IPFabricClient()
