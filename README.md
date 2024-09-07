# Configurik

**Configurik** is a Python library designed to simplify the process of loading and managing configuration files (YAML) with strong typing and custom logic. It also provides an **implementation registry** system, making it easier to create modular and pluggable components.

## Features

- Load and parse YAML configuration files.
- Typing supported.
- Custom parsing logic and validation for complex configurations.
- No redundant data is carried when not needed.
- **ImplRegistry** for modular and pluggable components.
- Easily extendable for different environments.

## Installation

```bash
pip install configurik
```

## Usage

### Defining Configurations

You can define your application configuration using `StaticConfig` and `VariableConfig` classes from the `cinfigurik` package.

`config/cache.py`
```python
from dataclasses import dataclass
from typing import Any, Dict
from configurable import VariableConfig, EmptyConfig

class CacheConfig(VariableConfig):
    pass

@dataclass
class Redis(CacheConfig):
    host: str
    port: int

    @classmethod
    def _parse(cls, raw: Dict[Any, Any]):
        return cls(
            host=raw["host"],
            port=int(raw["port"])
        )

@dataclass
class InMemory(EmptyConfig, CacheConfig):
    pass
```

`config/app.py`
```python
from dataclasses import dataclass
from typing import Any, Dict
from configurable import StaticConfig

from .cache import CacheConfig

@dataclass
class AppConfig(StaticConfig):
    cache: CacheConfig
    # and others...

    @classmethod
    def _parse(cls, raw: Dict[Any, Any]):
        return cls(
            cache=CacheConfig.construct_at(raw, "cache"),
        )
```

### Using `ImplRegistry`

**ImplRegistry** allows you to define a registry of implementations, so you can dynamically select the appropriate class based on the configuration. This is useful for creating pluggable architectures.

`cache.py`
```python
from abc import abstractmethod
from configurable import ImplRegistry
import config.cache

class Cache(ImplRegistry):

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    # This construct must always have a VariableConfig `config` arg
    # `config: config.cache.CacheConfig` in this case
    @classmethod
    async def construct(cls, config: config.cache.CacheConfig) -> "Cache":
        return await super().construct(config)

class Redis(Cache):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
    
    # This class will be chosen to be constructed from Cache.construct(config) if the config class name is `Redis`
    @classmethod
    async def construct(cls, config: config.cache.CacheConfig) -> Cache:
        assert isinstance(config, config.cache.Redis), f"{config} is not a config.cache.Redis"
        return cls(
            config.host,
            config.port,
        )

    def set(self, key: str, value: Any) -> None:
        print(f"Setting value in Redis at {self.host}:{self.port}")

    def get(self, key: str) -> Any:
        print(f"Getting value from Redis at {self.host}:{self.port}")

class InMemory(Cache):
    def __init__(self):
        self.store = {}
    
    # This class will be chosen to be constructed from Cache.construct(config) if the config class name is `InMemory`
    @classmethod
    async def construct(cls, config: CacheConfig) -> Agent:
        assert isinstance(config, config.cache.InMemory), f"{config} is not a config.cache.InMemory"
        return cls()

    def set(self, key: str, value: Any) -> None:
        self.store[key] = value
        print(f"Setting value in InMemory cache: {key}")

    def get(self, key: str) -> Any:
        return self.store.get(key, None)

```

In this example, the `Cache` class inherits from `ImplRegistry`, which allows you to construct the appropriate class based on the configuration through `Cache.construct(config)`.

### Example YAML Configuration

```yaml
# The configuration models (e.g. `redis`, `inmemory`) are resolved by using `<...>` with lowercase class name.
cache<redis>:
  host: "localhost"
  port: 6379

# and others...
```

### Parsing Configurations

You can load and parse your YAML configuration file using `load_config` and `StaticConfig.construct`.

`main.py`
```python
from cinfigurik import ParsingConfigException, load_config
import sys

from cache import Cache
from config.app import AppConfig

def parse_app_config(config_path: str) -> AppConfig:
    return AppConfig.construct(load_config(config_path), config_path)

async def main():
    try:
        config = parse_app_config("config.yml")
    except ParsingConfigException as e:
        print("Error in config file:", e)
        sys.exit(1)

    cache = await Cache.construct(config.cache)
    # now cache is either a redis or a inmemory cache

...
```