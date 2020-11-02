from typing import List, Dict, Any, Callable, Tuple, Optional
from abc import ABC
from operator import itemgetter


from ipf_netbox.log import get_logger


__all__ = ["Collection"]


class Collection(ABC):
    name = None
    source = None
    FINGERPRINT_FIELDS = None
    KEY_FIELDS = None

    def __init__(self):
        self.inventory: List[Any] = list()
        self.fingerprints: [List[Dict]] = list()
        self.keys: Dict[Tuple, Dict] = dict()

    async def fetch(self):
        pass

    def make_fingerprints(self, with_filter: Optional[Callable[[Dict], bool]] = None):
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

    def make_keys(self, *fields, with_translate=None):
        if not len(self.fingerprints):
            get_logger().warning("No fingerprints")
            return

        kf_getter = itemgetter(*(fields or self.KEY_FIELDS))
        self.keys.clear()
        with_translate = with_translate or (lambda x: x)

        self.keys.update(
            {with_translate(kf_getter(fp)): fp for fp in self.fingerprints}
        )
