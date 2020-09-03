from typing import Optional, List, Dict


from pydantic_env.models import NoExtraBaseModel


class DefaultsModel(NoExtraBaseModel):
    strip_domain_names: Optional[List[str]]


class SourceModel(NoExtraBaseModel):
    limit: Optional[List[str]]
    exclude: Optional[List[str]]


class ConfigModel(NoExtraBaseModel):
    defaults: DefaultsModel
    sources: Dict[str, SourceModel]