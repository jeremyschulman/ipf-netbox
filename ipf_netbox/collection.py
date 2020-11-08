from typing import List, Dict, Any, Callable, Tuple, Optional, Type
from abc import ABC
from operator import itemgetter


from ipf_netbox.log import get_logger
from ipf_netbox.source import Source

__all__ = ["Collector", "CollectionMixin", "CollectionCallback", "get_collection"]

CollectionCallback = Type[Callable[[Tuple, Any], None]]


class CollectionMixin(object):
    name = None
    source_class = None
    FINGERPRINT_FIELDS = None
    KEY_FIELDS = None

    async def fetch(self, **fetch_args):
        raise RuntimeError("Not implemented")

    async def fetch_keys(self, keys: Dict):
        raise RuntimeError("Not implemented")

    def fingerprint(self, rec: Dict) -> Dict:
        raise RuntimeError("Not implemented")

    async def create_missing(
        self, missing: Dict, callback: Optional[CollectionCallback] = None
    ):
        raise RuntimeError("Not implemented")

    async def update_changes(
        self, changes: Dict, callback: Optional[CollectionCallback] = None
    ):
        raise RuntimeError("Not implemented")


class Collector(ABC, CollectionMixin):
    def __init__(self, source: Source):

        # `source_records` is a list of recoreds as they are obtained from the
        # source.  The structure each source_records record is specific to the
        # source.  The inentory record is "fingerprinted" for collection fields;
        # which in turn are used to create inventory.

        self.source_records: List[Any] = list()

        # `inventory` is a dict where the key=<fields-key> and the value is the
        # fields-record of the source record.

        self.inventory: Dict[Tuple, Dict] = dict()

        # `source_record_keys` is a dict key=<fields-key>, value=<source-record>
        # that is used to cross reference the fields-key to a source specific
        # record ID which is typically found in the source specific response
        # record. The uid value is used when making updates to an exists record
        # in the source.

        self.source_record_keys: Dict[Tuple, Any] = dict()

        # The Source instance providing connectivity for the Collection
        # processing.

        self.source = source

        # `cache` is expected to be used by the subclass to store information
        # that it may need across various calls; for example caching device
        # records that may have information required by processing other
        # collections (ipaddrs).

        self.cache = dict()

    def make_keys(
        self,
        *fields,
        with_filter: Optional[Callable[[Dict], bool]] = None,
        with_translate=None,
        with_inventory=None,
    ):
        if not len(self.source_records):
            get_logger().info(
                f"Collection {self.name}:{self.source_class.__name__}: inventory empty."
            )
            return

        with_filter = with_filter if with_filter else lambda x: True
        with_translate = with_translate or (lambda x: x)

        kf_getter = itemgetter(*(fields or self.KEY_FIELDS))

        if not with_inventory:
            self.inventory.clear()

        for rec in with_inventory or self.source_records:
            try:
                fp = self.fingerprint(rec)
                if not with_filter(fp):
                    continue

            except Exception as exc:
                raise RuntimeError("Fingerprint failed", rec, exc)

            as_key = with_translate(kf_getter(fp))
            self.inventory[as_key] = fp
            self.source_record_keys[as_key] = rec

    @classmethod
    def get_collection(cls, source, name) -> "Collector":
        try:
            c_cls = next(
                iter(
                    c_cls
                    for c_cls in cls.__subclasses__()
                    if all(
                        (
                            c_cls.name == name,
                            c_cls.source_class,
                            isinstance(source, c_cls.source_class),
                        )
                    )
                )
            )

        except StopIteration:
            raise RuntimeError(
                f"NOT-FOUND: Collection {name} for source class: {source.name}"
            )

        return c_cls(source=source)

    def __len__(self):
        return len(self.source_records)


get_collection = Collector.get_collection
