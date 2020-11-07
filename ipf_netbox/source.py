import asyncio
from abc import ABC

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
            if (task := creator(key, item)) is None:
                continue

            tasks[task] = item
            task.add_done_callback(lambda _t: callback(tasks[_t], _t))

        await asyncio.gather(*tasks)


get_source = Source.get_source
