import io
import os
from dataclasses import dataclass
from configparser import ConfigParser
from typing import List, Dict, Type, Optional, Callable, Any

import pytz
import tzlocal

from console_tea import errors
from console_tea.enums import ConsoleFormat
from console_tea.singleton import Singleton
from console_tea.table import Column, RichTableMixin


@dataclass
class ConfigField:
    section: str
    option: str
    type: Type = str
    to_value: Optional[Callable[[Any], Any]] = None
    to_string: Optional[Callable[[Any], str]] = None


@dataclass()
class ConfigEntry(RichTableMixin):
    HEADERS = [
        Column(title="Key", path="key"),
        Column(title="Value", path="value"),
    ]
    key: str
    value: Any


class Config(Singleton):
    Format = ConsoleFormat

    ENTRIES: Dict[str, ConfigField] = {
        "debug": ConfigField(section="general", option="debug", type=bool),
        "format": ConfigField(
            section="general",
            option="format",
            to_value=ConsoleFormat,
            to_string=lambda v: v.value,
        ),
        "timezone": ConfigField(
            section="general",
            option="timezone",
            to_value=pytz.timezone,
            to_string=lambda v: v.zone,
        ),
        "log_dir": ConfigField(section="general", option="log_dir"),
    }

    def __init__(self, config_file):
        self._config_file = config_file
        self.debug = True
        self.format: ConsoleFormat = ConsoleFormat.text
        self.timezone = tzlocal.get_localzone()
        self.log_dir = os.path.join(os.path.dirname(config_file), "logs")

    @property
    def entries(self) -> List[ConfigEntry]:
        return [
            ConfigEntry(key=field, value=getattr(self, field))
            for field in self.ENTRIES
        ]

    def set(self, field, value):
        try:
            if field not in self.ENTRIES:
                raise ValueError(f"Invalid configuration key: {field}")

            entry = self.ENTRIES[field]
            if entry.type == bool:
                if value.lower() in ("true", "false", "on", "off"):
                    value = value.lower() in ("true", "on")
                else:
                    raise ValueError(f"Invalid boolean value: {value}")
            elif entry.type == int:
                value = int(value, 10)
            elif entry.type == float:
                value = float(value)

            if entry.to_value:
                value = entry.to_value(value)

            setattr(self, field, value)
        except ValueError as e:
            raise errors.InvalidConfiguration(
                key=f"{field}",
                value=value,
                operation=errors.InvalidConfiguration.Op.set,
                error=e,
            )

    def load(self):
        """Load configuration."""
        if not os.path.isfile(self._config_file):
            return
        try:
            cp = ConfigParser()
            cp.read(self._config_file)
        except Exception as e:
            raise errors.InvalidConfiguration(
                message=f"Cannot read the config file '{self._config_file}'. "
                f"Error: {e}"
            )

        for field, entry in self.ENTRIES.items():
            try:
                if cp.has_option(entry.section, entry.option):
                    self.set(field, cp.get(entry.section, entry.option))
            except errors.InvalidConfiguration:
                raise
            except Exception as e:
                raise errors.InvalidConfiguration(
                    key=f"{entry.section}.{entry.option}",
                    operation=errors.InvalidConfiguration.Op.load,
                    error=e,
                )

    def save(self):
        try:
            # Create if it doesn't exist
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            cp = ConfigParser()
            # If it already exists read the values
            if os.path.isfile(self._config_file):
                cp.read(self._config_file)

            for field, entry in self.ENTRIES.items():
                if not cp.has_section(entry.section):
                    cp.add_section(entry.section)

                value = getattr(self, field)
                value = (
                    entry.to_string(value)
                    if entry.to_string is not None
                    else str(value)
                )

                cp.set(entry.section, entry.option, value)

            with io.open(self._config_file, "w") as f:
                cp.write(f)
        except Exception as e:
            raise errors.InvalidConfiguration(
                operation=errors.InvalidConfiguration.Op.save, error=e
            )

    @classmethod
    def get_application_config(cls) -> "Config":
        subclasses = cls.__subclasses__()
        if len(subclasses) != 1:
            raise errors.InvalidConfiguration(
                "There should be only one subclass of Config."
            )
        return subclasses[0].instance
