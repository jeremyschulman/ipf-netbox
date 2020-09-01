from typing import Optional, Callable, Dict, List


def build_ipf_keys(ipf_inventory: List[Dict],
                   filter_: Optional[Callable[[Dict], bool]] = None):

    return {
        (rec['hostname'].lower(), rec['siteName'].lower())
        for rec in filter(filter_, ipf_inventory)
    }


def build_nb_keys(nb_inventory: List[Dict],
                  filter_: Optional[Callable[[Dict], bool]] = None):

    return {
        (rec['name'].lower(), rec['site']['slug'].lower())
        for rec in filter(filter_, nb_inventory)
    }


def audit(ipf_device_keys, nb_device_keys, resolve):
    nb_missing = ipf_device_keys - nb_device_keys
    print(nb_missing)
