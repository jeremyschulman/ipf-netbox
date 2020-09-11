from typing import Optional, List, Dict, Set, Hashable
from abc import ABC
from operator import itemgetter

from pydantic import BaseModel

__all__ = ['Collection']


class Collection(ABC):
    name = None
    FINGERPRINT_FIELDS = None
    KEY_FIELDS = None

    def __init__(self):
        self.inventory = None
        self.actions: Optional[List[Dict]] = None
        self.fingerprints: Optional[List[Dict]] = None
        self.keys: Optional[Set[Hashable]] = None

    async def fetch(self):
        raise NotImplemented()

    def make_fingerprints(self):
        self.fingerprints = [
            self.fingerprint(rec)
            for rec in self.inventory
        ]

    def fingerprint(self, rec: Dict) -> Dict:
        raise NotImplemented()

    def make_keys(self, fields=None):
        if not self.fingerprints:
            raise RuntimeError("Missing fingerprints")

        fieldsgetter = itemgetter(*(fields or self.KEY_FIELDS))
        self.keys = set(map(fieldsgetter, self.fingerprints))

    def audit(self, other_collection):
        raise NotImplemented()

    def reconcile(self):
        if not self.actions:
            raise RuntimeError("Missing audit actions")

