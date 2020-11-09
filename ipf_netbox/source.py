from abc import ABC
from typing import Coroutine

from .igather import igather


__all__ = ["Source", "get_source"]


class Source(ABC):
    name = None
    client_class = None

    def __init__(self):
        self.client = self.client_class()

    @classmethod
    def get_source(cls, name):
        try:
            s_cls = next(
                iter(s_cls for s_cls in cls.__subclasses__() if s_cls.name == name)
            )

        except StopIteration:
            raise RuntimeError(f"NOT-FOUND: Source name: {name}")

        return s_cls()

    @staticmethod
    async def update(updates, callback, creator):

        tasks = dict()
        callback = callback or (lambda _k, _t: True)

        for key, item in updates.items():
            if (coro := creator(key, item)) is None:
                continue

            if not isinstance(coro, Coroutine):
                raise RuntimeError("Source.update requires a coroutine")

            tasks[coro] = item

        async for orig_coro, res in igather(tasks, limit=100):
            item = tasks[orig_coro]
            callback(item, res)


get_source = Source.get_source
