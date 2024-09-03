from abc import abstractmethod
from dataclasses import dataclass
import os
import re
from string import Template
from typing import Any, Dict
from yaml import full_load
from dotenv import load_dotenv


@dataclass
class ConfImplBody:
    impl: str
    body: Any

    @classmethod
    def apply(cls, raw: Any) -> Any:
        if isinstance(raw, dict):
            res = {}

            for k, v in raw.items():  # type: ignore
                if isinstance(k, str):
                    match = re.match(r"([^<]+)<([^>]+)>", k)
                    if match is not None:
                        res[match.group(1)] = ConfImplBody(
                            match.group(2),
                            ConfImplBody.apply(v),
                        )
                        continue
                res[k] = ConfImplBody.apply(v)

            return res  # type: ignore

        elif isinstance(raw, list):
            return [ConfImplBody.apply(e) for e in raw]  # type: ignore

        return raw


def inject_environs(raw: Any) -> Any:
    if isinstance(raw, dict):
        return {inject_environs(k): inject_environs(v) for k, v in raw.items()}  # type: ignore

    elif isinstance(raw, list):
        return [inject_environs(e) for e in raw]  # type: ignore

    elif isinstance(raw, str):
        return Template(raw).safe_substitute(os.environ)

    return raw


class ParsingConfigException(Exception):
    def __init__(self, at: str, e: Exception) -> None:
        self.at = at
        self.e = e

    def __repr__(self) -> str:
        return f"{self.at} > {self.e}"

    def __str__(self) -> str:
        return self.__repr__()


class _ConstructableConfig:
    @classmethod
    def construct_at(cls, raw: Dict[Any, Any], at: str):
        assert isinstance(raw, dict), "expected a dict"
        return cls.construct(raw[at], at)

    @classmethod
    @abstractmethod
    def construct(cls, raw: Any, at: str) -> Any: ...


class _ParsableConfig:
    @classmethod
    @abstractmethod
    def _parse(cls, raw: Any) -> Any: ...

    @staticmethod
    def _construct(clas: type["_ParsableConfig"], raw: Any, at: str):
        try:
            return clas._parse(raw)
        except KeyError as e:
            raise ParsingConfigException(
                at, Exception(f"Expected to find key: {e}")
            ) from e
        except Exception as e:
            raise ParsingConfigException(at, e) from e


class StaticConfig(_ConstructableConfig, _ParsableConfig):
    @classmethod
    def construct(cls, raw: Any, at: str):
        return _ParsableConfig._construct(cls, raw, at)


class VariableConfig(_ConstructableConfig, _ParsableConfig):
    _impls: Dict[str, type[_ConstructableConfig]]

    @classmethod
    def construct(cls, raw: Any, at: str):
        try:
            if isinstance(raw, ConfImplBody):
                impl = cls._impls.get(raw.impl)

                if impl is None:
                    raise ValueError(f'Impl "{raw.impl}" not found')

                return impl.construct(raw.body, f"{raw.impl}")

            else:
                raise ValueError("Impl key is not provided")

        except Exception as e:
            raise ParsingConfigException(at, e) from e

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        if hasattr(cls, "_impls"):
            cls.construct = lambda raw, at: _ParsableConfig._construct(cls, raw, at)
            cls._impls[cls.__qualname__.lower()] = cls
        else:
            cls._impls = {}


load_dotenv()


def load_config(config_path: str):
    with open(config_path, "r") as f:
        data = full_load(f)
    return ConfImplBody.apply(inject_environs(data))
