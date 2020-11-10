from typing import Dict, Callable, Optional
from collections import namedtuple

from ipf_netbox.collection import Collector

Changes = namedtuple("Changes", ["fingerprint", "fields"])
DiffResults = namedtuple("DiffResults", ["missing", "extras", "changes"])


def diff(
    source_from: Collector,
    sync_to: Collector,
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
    DiffResults:
        missing: Dict[Tuple]
        changes: List[Tuple[Dict, Dict]]
    """
    sync_to_keys = set(sync_to.inventory)
    source_from_keys = set(source_from.inventory)

    missing_keys = source_from_keys - sync_to_keys
    extra_keys = sync_to_keys - source_from_keys
    shared_keys = source_from_keys & sync_to_keys

    # missing key dict; key=source_records-key, value=key-fingerprint
    missing_key_items = {key: source_from.inventory[key] for key in missing_keys}
    extra_key_items = {key: sync_to.inventory[key] for key in extra_keys}

    changes = dict()

    if not fields_cmp:
        fields_cmp = {}

    for field in source_from.FINGERPRINT_FIELDS:
        if field not in fields_cmp:
            fields_cmp[field] = lambda f: f

    for key in shared_keys:
        source_fp = source_from.inventory[key]
        sync_fp = sync_to.inventory[key]

        item_changes = dict()

        for field, field_fn in fields_cmp.items():
            if field_fn(source_fp[field]) != field_fn(sync_fp[field]):
                item_changes[field] = source_fp[field]

        if len(item_changes):
            changes[key] = Changes(sync_fp, item_changes)

    if not any((missing_key_items, extra_key_items, changes)):
        return None

    return DiffResults(
        missing=missing_key_items, changes=changes, extras=extra_key_items
    )
