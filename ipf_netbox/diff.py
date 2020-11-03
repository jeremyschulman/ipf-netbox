from typing import Dict, Callable, Optional
from collections import namedtuple

from ipf_netbox.collection import Collection

MissingKeyItem = namedtuple("MissingKeyItem", ["key", "other_fp"])
ChangeItem = namedtuple("ChangedItem", ["source_fp", "changes"])
DiffResults = namedtuple("DiffResults", ["missing", "changes"])


def diff(
    source_from: Collection,
    sync_to: Collection,
    fields_cmp: Optional[Dict[str, Callable]] = None,
):
    """
    The source and other collections have already been fetched, fingerprinted, and keyed.
    This method is used to create a diff report so that action can be taken to account for
    the differences.

    Parameters
    ----------
    source_from:
        The collection that is the source of truth for the diff

    sync_to:
        The collection that represents the destination of the update

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
    sync_to_keys = set(sync_to.keys)
    source_from_keys = set(source_from.keys)

    missing_keys = source_from_keys - sync_to_keys
    shared_keys = source_from_keys & sync_to_keys

    missing_key_items = [
        MissingKeyItem(key, source_from.keys[key]) for key in missing_keys
    ]

    changes = list()

    if not fields_cmp:
        fields_cmp = {field: lambda f: f for field in source_from.FINGERPRINT_FIELDS}

    for key in shared_keys:
        source_fp = source_from.keys[key]
        other_fp = sync_to.keys[key]

        item_changes = dict()

        for field, field_fn in fields_cmp.items():
            if field_fn(source_fp[field]) != field_fn(other_fp[field]):
                item_changes[field] = other_fp[field]

        if len(item_changes):
            changes.append(ChangeItem(source_fp, item_changes))

    return DiffResults(missing=missing_key_items, changes=changes)
