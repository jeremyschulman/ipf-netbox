# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import CollectionMixin

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["IPAddrCollection"]


class IPAddrCollection(CollectionMixin):
    name = "ipaddrs"

    FINGERPRINT_FIELDS = ("ipaddr", "interface", "hostname")

    KEY_FIELDS = (
        "hostname",
        "ipaddr",
    )
