from ipf_netbox.collection import CollectionMixin


class SiteCollection(CollectionMixin):
    name = "sites"

    FINGERPRINT_FIELDS = ("name",)
    KEY_FIELDS = ("name",)
