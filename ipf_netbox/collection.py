from typing import List, Dict, Any, Callable, Tuple, Optional
from abc import ABC
from operator import itemgetter


from ipf_netbox.log import get_logger


__all__ = ["Collection", "CollectionMixin", "get_collection"]


class CollectionMixin(object):
    name = None
    source_class = None
    FINGERPRINT_FIELDS = None
    KEY_FIELDS = None


class Collection(ABC, CollectionMixin):
    def __init__(self, source):

        # `inventory` is a list of recoreds as they are obtained from the
        # source.  The structure each inventory record is specific to the
        # source.  The inentory record is "fingerprinted" for collection fields;
        # which in turn are used to create keys.

        self.inventory: List[Any] = list()

        # the keys created from the inventory.  this is a dict where the
        # key=<fp-key> and the value is the fingerprint record of the collection
        # fields.

        self.keys: Dict[Tuple, Dict] = dict()

        # `uids` is a dict key=<fingerprint-key>, value=<source unique-id> that
        # is used to cross reference the fp-key to a source specific record ID
        # which is typically found in the source specific response record. The
        # uid value is used when making updates to an exists record in the
        # source.

        self.uids: Dict[Tuple, Any] = dict()
        self.source = source

    async def fetch(self, **fetch_args):
        pass

    async def catalog(
        self,
        *fields,
        with_fetchargs: Optional[Dict] = None,
        with_filter: Optional[Callable[[Dict], bool]] = None,
        with_translate: Optional[Callable] = None,
    ):
        self.inventory = await self.fetch(**(with_fetchargs or {}))
        # self.make_fingerprints(with_filter=with_filter)
        self.make_keys(*fields, with_filter=with_filter, with_translate=with_translate)

    # def make_fingerprints(self, with_filter: Optional[Callable[[Dict], bool]] = None):
    #     if not len(self.inventory):
    #         get_logger().info(
    #             f"Collection {self.name}:{self.source_class.__name__}: No inventory"
    #         )
    #         return
    #
    #     with_filter = with_filter if with_filter else lambda x: True
    #
    #     self.fingerprints.clear()
    #     for rec in self.inventory:
    #         try:
    #             fp = self.fingerprint(rec)
    #         except Exception as exc:
    #             raise RuntimeError("Fingerprint failed", rec, exc)
    #
    #         if with_filter(fp):
    #             self.fingerprints.append(fp)

    def fingerprint(self, rec: Dict) -> Dict:
        pass

    def make_keys(
        self,
        *fields,
        with_filter: Optional[Callable[[Dict], bool]] = None,
        with_translate=None,
        with_inventory=None,
    ):
        if not len(self.inventory):
            get_logger().info(
                f"Collection {self.name}:{self.source_class.__name__}: inventory empty."
            )
            return

        with_filter = with_filter if with_filter else lambda x: True
        with_translate = with_translate or (lambda x: x)

        kf_getter = itemgetter(*(fields or self.KEY_FIELDS))

        if not with_inventory:
            self.keys.clear()

        for rec in with_inventory or self.inventory:
            try:
                uid, fp = self.fingerprint(rec)
                if not with_filter(fp):
                    continue

            except Exception as exc:
                raise RuntimeError("Fingerprint failed", rec, exc)

            as_key = with_translate(kf_getter(fp))
            self.keys[as_key] = fp
            self.uids[as_key] = uid

    @classmethod
    def get_collection(cls, source, name):
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
        return len(self.inventory)


get_collection = Collection.get_collection
