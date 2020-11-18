from ipf_netbox.source import Source
from aioipfabric.client import IPFabricClient

NAME = "ipfabric"

__all__ = ["IPFabricSource", "IPFabricClient"]


class IPFabricSource(Source):
    name = NAME
    client_class = IPFabricClient
