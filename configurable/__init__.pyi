from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class ConfImplBody:
    impl: str
    body: Any

    @classmethod
    def apply(cls, raw: Any) -> Any: ...

def inject_environs(raw: Any) -> Any: ...

class ParsingConfigException(Exception):
    at: str
    e: Exception

    def __init__(self, at: str, e: Exception) -> None: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...

class _ConstructableConfig:
    @classmethod
    def construct_at(cls, raw: Dict[Any, Any], at: str) -> Any: ...
    @classmethod
    @abstractmethod
    def construct(cls, raw: Any, at: str) -> Any: ...

class _ParsableConfig:
    @classmethod
    @abstractmethod
    def _parse(cls, raw: Any) -> Any: ...
    @staticmethod
    def _construct(clas: type["_ParsableConfig"], raw: Any, at: str) -> Any: ...

class StaticConfig(_ConstructableConfig, _ParsableConfig):
    @classmethod
    def construct(cls, raw: Any, at: str) -> Any: ...

class VariableConfig(_ConstructableConfig, _ParsableConfig):
    _impls: Dict[str, type[_ConstructableConfig]]

    @classmethod
    def construct(cls, raw: Any, at: str) -> Any: ...
    def __init_subclass__(cls, **kwargs: Any) -> None: ...

def load_config(config_path: str) -> Any: ...
