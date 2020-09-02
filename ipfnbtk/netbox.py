import asyncio
from os import environ
from operator import itemgetter
from functools import cached_property


from httpx import AsyncClient


class NetboxClient(AsyncClient):
    ENV_VARS = ["NETBOX_ADDR", "NETBOX_TOKEN"]

    def __init__(self):
        try:
            url, token = itemgetter(*NetboxClient.ENV_VARS)(environ)
        except KeyError as exc:
            raise RuntimeError(f"Missing environment variable: {exc.args[0]}")

        super().__init__(
            base_url=f"{url}/api",
            headers=dict(Authorization=f"Token {token}"),
            verify=False,
        )

    @cached_property
    def devices(self):
        return asyncio.get_event_loop().run_until_complete(self.fetch_devices())

    async def fetch_devices(self, timeout=60):
        res = await self.get(
            "/dcim/devices",
            timeout=timeout,
            params={"limit": 0, "exclude": "config_context", 'platform__n': 'null'},
        )
        res.raise_for_status()
        body = res.json()
        devices = body["results"]
        assert body["count"] == len(devices)
        return devices
