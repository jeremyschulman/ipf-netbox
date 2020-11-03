# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.collection import CollectionMixin

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["DeviceCollection"]


class DeviceCollection(CollectionMixin):
    name = "devices"

    FINGERPRINT_FIELDS = (
        "sn",
        "hostname",
        "ipaddr",
        "site",
        "os_name",
        "vendor",
        "model",
    )

    KEY_FIELDS = ("sn",)
