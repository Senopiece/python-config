from abc import abstractmethod
from dataclasses import dataclass
import os
import re
from string import Template
from typing import Any, Dict
from yaml import full_load
from dotenv import load_dotenv


class ImplRegistry:
    _impls: Dict[str, type["ImplRegistry"]]

    @classmethod
    def construct(cls, config: Any, *args: Any, **kwargs: Any) -> Any:
        return cls._impls[config.__class__.__qualname__.lower()].construct(
            config, *args, **kwargs
        )

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        if hasattr(cls, "_impls"):

            base = cls.__base__
            assert base is not None and issubclass(
                base, ImplRegistry
            ), f"{cls} must inherit from ImplRegistry"

            if cls.construct.__code__ == base.construct.__code__:
                raise NotImplementedError(f"{cls}.construct(...) is not implemented")

            cls._impls[cls.__qualname__.lower()] = cls
        else:
            cls._impls = {}


class EmptyConfig:
    @classmethod
    def _parse(cls, raw: None):
        assert raw is None, "expected a null"
        return cls()


@dataclass
class _ConfImplBody:
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
                        res[match.group(1)] = _ConfImplBody(
                            match.group(2),
                            _ConfImplBody.apply(v),
                        )
                        continue
                res[k] = _ConfImplBody.apply(v)

            return res  # type: ignore

        elif isinstance(raw, list):
            return [_ConfImplBody.apply(e) for e in raw]  # type: ignore

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
            if isinstance(raw, _ConfImplBody):
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


def _inject_environs(raw: Any) -> Any:
    if isinstance(raw, dict):
        return {_inject_environs(k): _inject_environs(v) for k, v in raw.items()}  # type: ignore

    elif isinstance(raw, list):
        return [_inject_environs(e) for e in raw]  # type: ignore

    elif isinstance(raw, str):
        return Template(raw).safe_substitute(os.environ)

    return raw


def load_config(config_path: str):
    with open(config_path, "r") as f:
        data = full_load(f)
    return _ConfImplBody.apply(_inject_environs(data))


load_dotenv()
