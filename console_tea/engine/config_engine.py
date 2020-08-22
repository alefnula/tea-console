from typing import List

from console_tea import errors
from console_tea.config import ConfigEntry, Config


class ConfigEngine:
    @staticmethod
    def list() -> List[ConfigEntry]:
        """List all configuration values."""
        config = Config.get_application_config()
        return config.entries

    @classmethod
    def set(cls, key: str, value: str):
        config = Config.get_application_config()
        try:
            config.set(field=key, value=value)
            config.save()
            return cls.list()
        except Exception as e:
            raise errors.InvalidConfiguration(
                key=key,
                value=value,
                error=e,
                operation=errors.InvalidConfiguration.Op.set,
            )
