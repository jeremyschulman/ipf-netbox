from .collection import Collection

import jsonpatch


def diff(source: Collection, other: Collection, ignore_fields=None):
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

    ignore_fields:
        List of fingerprint fields to ignore during comparison process

    Returns
    -------
    Tuple
        missing_key_items: List
        changes: List
    """
    other_keys = set(other.keys)
    source_keys = set(source.keys)

    missing_keys = other_keys - source_keys
    shared_keys = source_keys & other_keys

    missing_key_items = [(key, other.keys[key]) for key in missing_keys]

    changes = list()

    if ignore_fields:
        ignore_fields = ["/_id"] + ["/" + field for field in ignore_fields]
    else:
        ignore_fields = ["/_id"]

    for key in shared_keys:
        source_fp = source.keys[key]
        other_fp = other.keys[key]

        patch = jsonpatch.make_patch(source_fp, other_fp).patch

        if len(
            item_changes := {
                item["path"][1:]: item["value"]
                for item in patch
                if item["op"] == "replace" and item["path"] not in ignore_fields
            }
        ):
            changes.append((source_fp, item_changes))

    return missing_key_items, changes
