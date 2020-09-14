from typing import Dict, Callable
from collections import namedtuple

from .collection import Collection

MissingKeyItem = namedtuple("MissingKeyItem", ["key", "other_fp"])
ChangeItem = namedtuple("ChangedItem", ["source_fp", "changes"])


def diff(source: Collection, other: Collection, fields_cmp: Dict[str, Callable]):
    """
    The source and other collections have already been fetched, fingerprinted, and keyed.
    This method is used to create a diff report so that action can be taken to account for
    the differences.

    Parameters
    ----------
    source:
        The source collection is the one that would be updated after the diff.

    other:
        The other collection that is used to compare differences against the source.

    fields_cmp:
        Dictionary mapping the field name to a function used to "normalize" the
        value so that it can be compared.  A common function would be
        `str.lower` to convert a field (hostname) to lower for comparison
        purposes.

    Returns
    -------
    Tuple
        missing_key_items: List[Tuple]
        changes: List[Tuple[Dict, Dict]]
    """
    other_keys = set(other.keys)
    source_keys = set(source.keys)

    missing_keys = other_keys - source_keys
    shared_keys = source_keys & other_keys

    missing_key_items = [MissingKeyItem(key, other.keys[key]) for key in missing_keys]

    changes = list()

    for key in shared_keys:
        source_fp = source.keys[key]
        other_fp = other.keys[key]

        item_changes = dict()

        for field, field_fn in fields_cmp.items():
            if field_fn(source_fp[field]) != field_fn(other_fp[field]):
                item_changes[field] = other_fp[field]

        if len(item_changes):
            changes.append(ChangeItem(source_fp, item_changes))

    return missing_key_items, changes
