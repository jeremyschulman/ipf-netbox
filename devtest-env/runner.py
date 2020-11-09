import os
import asyncio

from ipf_netbox.source import get_source
from ipf_netbox.collection import get_collection
from ipf_netbox.config import load_config_file

load_config_file(filepath=open(os.getenv("IPF_NETBOX_CONFIG")))

ipf_col_pc = get_collection(source=get_source("ipfabric"), name="portchans")
nb_col_pc = get_collection(source=get_source("netbox"), name="portchans")


async def run(**params):
    async with ipf_col_pc.source.client, nb_col_pc.source.client:
        await ipf_col_pc.fetch(**params)
        ipf_col_pc.make_keys()

        hostname_list = {rec["hostname"] for rec in ipf_col_pc.inventory.values()}

        await asyncio.gather(
            *(nb_col_pc.fetch(hostname=hostname) for hostname in hostname_list)
        )

        nb_col_pc.make_keys()
