# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import CollectionMixin

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["InterfaceCollection"]


class InterfaceCollection(CollectionMixin):
    name = "interfaces"

    FINGERPRINT_FIELDS = ("hostname", "interface", "description")

    KEY_FIELDS = ("hostname", "interface")
