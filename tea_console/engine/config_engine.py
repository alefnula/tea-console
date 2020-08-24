from typing import List, Dict
from tea_console import errors
from tea_console.config import ConfigEntry, Config


class ConfigEngine:
    @staticmethod
    def list() -> Dict[str, List[ConfigEntry]]:
        """List all configuration values."""
        config = Config.get_application_config()
        return config.entries

    @classmethod
    def set(cls, key: str, value: str):
        config = Config.get_application_config()
        if key.count(".") != 1:
            raise ValueError(
                f"Invalid configuration key: {key}. "
                f"Valid format: `section.option`"
            )
        section, option = key.split(".")
        try:
            for key, field in config.ENTRIES.items():
                if field.section == section and field.option == option:
                    config.set(field=key, value=value)
                    config.save()
                    break
        except errors.InvalidConfiguration:
            raise
        except Exception as e:
            raise errors.InvalidConfiguration(
                key=key,
                value=value,
                error=e,
                operation=errors.InvalidConfiguration.Op.set,
            )
