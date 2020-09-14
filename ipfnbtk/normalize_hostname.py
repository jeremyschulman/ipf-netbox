# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from functools import partial, lru_cache
import re

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from ipfnbtk.config import g_config, ConfigModel

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
    cfg_obj: ConfigModel = g_config.get()
    any_domain = "|".join(map(re.escape, cfg_obj.defaults.strip_domain_names))
    return partial(re.compile(any_domain).sub, repl="")


def normalize_hostname(hostname):
    return domain_remover()(string=hostname.lower())
