from typing import Dict

from aioipfabric.filters import parse_filter
from aioipfabric.mixins.portchan import IPFPortChannels

from ipf_netbox.collection import Collector
from ipf_netbox.collections.portchans import PortChannelCollection
from ipf_netbox.ipfabric.source import IPFabricSource, IPFabricClient

from ipf_netbox.mappings import expand_interface, normalize_hostname


class IPFabricPortChannelCollection(Collector, PortChannelCollection):
    source_class = IPFabricSource

    async def fetch(self, **params):

        api: IPFabricClient(IPFPortChannels) = self.source.client
        api.mixin(IPFPortChannels)

        if (filters := params.get("filters")) is not None:
            params["filters"] = parse_filter(filters)

        records = await api.fetch_portchannels(**params)
        api.xf_portchannel_members(records)

        # invert these records to a flat list of fields.

        xf_records = [
            dict(
                hostname=rec["hostname"],
                intName=member["intName"],
                portchan=rec["intName"],
            )
            for rec in records
            for member in rec["members"]
        ]

        self.source_records.extend(xf_records)

    def fingerprint(self, rec: Dict) -> Dict:
        return dict(
            hostname=normalize_hostname(rec["hostname"]),
            interface=expand_interface(rec["intName"]),
            portchan=expand_interface(rec["portchan"]),
        )
