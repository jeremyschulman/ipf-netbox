from typing import List, Dict, Set, Hashable, Any, Callable
from abc import ABC
from operator import itemgetter


from ipfnbtk.log import get_logger


__all__ = ["Collection"]


class Collection(ABC):
    name = None
    source = None
    FINGERPRINT_FIELDS = None
    KEY_FIELDS = None

    def __init__(self):
        self.inventory: List[Any] = list()
        self.fingerprints: [List[Dict]] = list()
        self.keys: [Set[Hashable]] = set()

    async def fetch(self):
        pass

    def make_fingerprints(self, with_filter: Callable[[Dict], bool]):
        if not len(self.inventory):
            get_logger().warning("No inventory")
            return

        with_filter = with_filter if with_filter else lambda x: True

        self.fingerprints.clear()
        for rec in self.inventory:
            try:
                fp = self.fingerprint(rec)
            except Exception as exc:
                raise RuntimeError("Fingerprint failed", rec, exc)

            if with_filter(fp):
                self.fingerprints.append(fp)

    def fingerprint(self, rec: Dict) -> Dict:
        pass

    def make_keys(self, fields=None):
        if not len(self.fingerprints):
            get_logger().warning("No fingerprints")
            return

        fieldsgetter = itemgetter(*(fields or self.KEY_FIELDS))
        self.keys = set(map(fieldsgetter, self.fingerprints))

    def audit(self, other):
        pass

    def reconcile(self):
        pass
