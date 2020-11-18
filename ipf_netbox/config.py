import os
from typing import TextIO
from contextvars import ContextVar

import toml

from pydantic import ValidationError
from pydantic_env import config_validation_errors
from .config_models import ConfigModel
from ipf_netbox import consts


__all__ = ["get_config", "load_config_file", "load_default_config_file", "ConfigModel"]

g_config = ContextVar("config")


def get_config() -> ConfigModel:
    return g_config.get()


def load_config_file(filepath: TextIO):
    try:
        config_obj = ConfigModel.parse_obj(toml.load(filepath))
        g_config.set(config_obj)
        return config_obj

    except ValidationError as exc:
        raise RuntimeError(
            config_validation_errors(errors=exc.errors(), filepath=filepath.name)
        )


def load_default_config_file():
    cfg_file = os.environ.get(consts.ENV_CONFIG_FILE, consts.DEFAULT_CONFIG_FILE)
    load_config_file(filepath=open(cfg_file))
