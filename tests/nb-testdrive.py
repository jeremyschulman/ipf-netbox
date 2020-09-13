import asyncio

from ipfnbtk.collections.devices import DeviceCollection  # noqa
from ipfnbtk.sources.netbox import NetboxDeviceCollection
from ipfnbtk.sources.netbox.client import get_client
from ipfnbtk.filtering import create_filter

loop = asyncio.get_event_loop()
asyncio.set_event_loop(loop)

nb = get_client()
nb_dc = NetboxDeviceCollection()


filter_func = create_filter(['status=(active|offline|staging)'], field_names=['status'])


loop.run_until_complete(nb_dc.fetch())
