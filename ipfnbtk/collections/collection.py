from typing import Optional, List, Dict, Set, Hashable
from abc import ABC
from operator import itemgetter


__all__ = ["Collection"]


class Collection(ABC):
    name = None
    FINGERPRINT_FIELDS = None
    KEY_FIELDS = None

    def __init__(self):
        self.inventory = None
        self.fingerprints: [List[Dict]] = list()
        self.keys: Optional[Set[Hashable]] = None

    async def fetch(self):
        raise NotImplementedError()

    def make_fingerprints(self):
        self.fingerprints.clear()
        for rec in self.inventory:
            try:
                self.fingerprints.append(self.fingerprint(rec))
            except Exception as exc:
                raise RuntimeError("Fingerprint failed", rec, exc)

    def fingerprint(self, rec: Dict) -> Dict:
        raise NotImplementedError()

    def make_keys(self, fields=None):
        if not self.fingerprints:
            raise RuntimeError("Missing fingerprints")

        fieldsgetter = itemgetter(*(fields or self.KEY_FIELDS))
        self.keys = set(map(fieldsgetter, self.fingerprints))

    def audit(self, other_collection):
        pass

    def reconcile(self):
        pass
