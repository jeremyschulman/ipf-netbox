from functools import wraps
from ipf_netbox.source import get_source


def with_sources(coro):
    @wraps(coro)
    async def wrapper(*vargs, **kwargs):
        nb_src = get_source("netbox")
        ipf_src = get_source("ipfabric")

        async with nb_src.client, ipf_src.client:
            ipf_src.client.timeout = 60
            nb_src.client.timeout = 60

            await coro(ipf_src, nb_src, *vargs, **kwargs)

    return wrapper
