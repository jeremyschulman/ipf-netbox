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
        self.source_records.extend(records)

    def fingerprint(self, rec: Dict) -> Dict:
        return {
            "interface": expand_interface(rec["intName"]),
            "hostname": normalize_hostname(rec["hostname"]),
            "members": {
                expand_interface(member["intName"]) for member in rec["members"]
            },
        }
