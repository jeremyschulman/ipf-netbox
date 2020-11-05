# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from functools import partial, lru_cache
import re

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipf_netbox.config import get_config

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["normalize_hostname"]


# -----------------------------------------------------------------------------
#
#                              CODE BEGINS
#
# -----------------------------------------------------------------------------


@lru_cache()
def domain_remover():
    cfg_obj = get_config()
    any_domain = "|".join(map(re.escape, cfg_obj.defaults.domain_names))
    return partial(re.compile(any_domain).sub, repl="")


def normalize_hostname(hostname):
    return domain_remover()(string=hostname.lower())
