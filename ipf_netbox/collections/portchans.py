# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import CollectionMixin

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["PortChannelCollection"]


class PortChannelCollection(CollectionMixin):
    name = "portchans"

    FINGERPRINT_FIELDS = ("hostname", "interface", "portchan")

    KEY_FIELDS = ("hostname", "interface")
