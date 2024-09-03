from dataclasses import dataclass
from typing import Any, Dict
from config import StaticConfig, VariableConfig, load_config


class BotConfig(VariableConfig):
    pass


@dataclass
class Pyro(BotConfig):
    token: str
    app_id: int
    app_hash: str

    @classmethod
    def _parse(cls, raw: Dict[Any, Any]):
        assert isinstance(raw, dict), "expected a dict"
        res = cls(
            token=raw["token"],
            app_id=raw["app:id"],
            app_hash=raw["app:hash"],
        )
        assert isinstance(res.token, str), "'token' must be a string"
        assert isinstance(res.app_id, int), "'app:id' must be a int"
        assert isinstance(res.app_hash, str), "'app:hash' must be a string"
        return res


class AgentConfig(VariableConfig):
    pass


@dataclass
class Anthropic(AgentConfig):
    model: str
    proxy: str | None
    key: str

    @classmethod
    def _parse(cls, raw: Dict[Any, Any]):
        assert isinstance(raw, dict), "expected a dict"
        res = cls(
            model=raw["model"],
            proxy=raw.get("proxy"),
            key=raw["key"],
        )
        assert isinstance(res.model, str), "'model' must be a string"
        assert (
            isinstance(res.proxy, str) or res.proxy is None
        ), "'proxy' must be a string or null"
        assert isinstance(res.key, str), "'key' must be a string"
        return res


@dataclass
class AppConfig(StaticConfig):
    bot: BotConfig
    agent: AgentConfig

    @classmethod
    def _parse(cls, raw: Dict[Any, Any]):
        assert isinstance(raw, dict), "expected a dict"
        return cls(
            bot=BotConfig.construct_at(raw, "bot"),
            agent=AgentConfig.construct_at(raw, "agent"),
        )


def parse_app_config(config_path: str):
    return AppConfig.construct(load_config(config_path), config_path)


try:
    print(parse_app_config("example.yml"))
except Exception as e:
    print(e)
