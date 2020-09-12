from typing import Optional, Dict, List
import asyncio
from os import environ
from operator import itemgetter
from itertools import chain
from functools import lru_cache


from httpx import AsyncClient


class NetboxClient(AsyncClient):
    ENV_VARS = ["NETBOX_ADDR", "NETBOX_TOKEN"]
    DEFAULT_PAGE_SZ = 100

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

    async def paginate(
        self, url: str, page_sz: Optional[int] = None, filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Concurrently paginate GET on url for the given page_sz and optional
        Caller filters (Netbox API specific).  Return the list of all page
        results.

        Parameters
        ----------
        url:
            The Netbox API URL endpoint

        page_sz:
            Max number of result items

        filters:
            The Netbox API params filter options.

        Returns
        -------
        List of all Netbox API results from all pages
        """

        # GET the url for limit = 1 record just to determin the total number of
        # items.

        params = filters or {}
        params["limit"] = 1

        res = await self.get(url, params=params)
        res.raise_for_status()
        body = res.json()
        count = body["count"]

        # create a list of tasks to run concurrently to fetch the data in pages.
        # NOTE: that we _MUST_ do a params.copy() to ensure that each task has a
        # unique offset count.  Observed that if copy not used then all tasks have
        # the same (last) value.

        params["limit"] = page_sz or self.DEFAULT_PAGE_SZ
        tasks = list()

        for offset in range(0, count, params["limit"]):
            params["offset"] = offset
            tasks.append(self.get(url, params=params.copy()))

        task_results = await asyncio.gather(*tasks)

        # return the flattened list of results

        return list(
            chain.from_iterable(task_r.json()["results"] for task_r in task_results)
        )


@lru_cache()
def get_client():
    nb = NetboxClient()
    nb.timeout = 30
    return nb
