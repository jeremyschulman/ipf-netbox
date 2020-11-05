from typing import Callable
from functools import lru_cache
from ipf_netbox.config import get_config
import re


@lru_cache()
def expaner_os(os_name) -> Callable[[str], str]:
    config = get_config()
    cfg_map = config.maps["interfaces"][os_name]
    mapper = re.compile(r"|".join(list(cfg_map)))

    def _expander(ifname):
        return mapper.sub(lambda mo: cfg_map[mo.group(0)], ifname)

    return _expander


def expand_interface(os_name: str, ifname: str) -> str:
    return expaner_os(os_name)(ifname)
