import io
import os
import json
from dataclasses import dataclass
from collections import defaultdict
from configparser import ConfigParser
from typing import List, Dict, Optional, Callable, Any, Type

import pytz
import tzlocal
from tea.dsa.singleton import Singleton

from tea_console import errors
from tea_console.enums import ConsoleFormat
from tea_console.table import Column, RichTableMixin


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


class TeaConsoleConfig(Singleton):
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
        self.load()
        self.save()

    @property
    def entries(self) -> Dict[str, List[ConfigEntry]]:
        result = defaultdict(list)
        for key, field in self.ENTRIES.items():
            result[field.section].append(
                ConfigEntry(key=field.option, value=self.get(key))
            )
        return result

    def set(self, field: str, value: str):
        """Set field value from string."""
        try:
            if field not in self.ENTRIES:
                raise ValueError(f"Invalid configuration key: {field}")

            entry = self.ENTRIES[field]
            # Quote string if it's not already quoted
            if (
                entry.type == str
                and not (value.startswith('"') and value.endswith('"'))
                and value.strip().lower() != "null"
            ):
                value = fr'"{value}"'

            # Load the value
            try:
                value = json.loads(value)
            except Exception:
                raise ValueError(
                    f"Cannot parse '{value}' as '{entry.type.__name__}'."
                )
            if value is not None and not isinstance(value, entry.type):
                raise ValueError(
                    f"Type mismatch. {entry.type.__name__} != "
                    f"{type(value).__name__}"
                )
            if entry.to_value is not None:
                value = entry.to_value(value)
            setattr(self, field, value)
        except ValueError as e:
            raise errors.InvalidConfiguration(
                key=f"{field}",
                value=value,
                operation=errors.InvalidConfiguration.Op.set,
                error=e,
            )

    def get(self, field: str) -> str:
        """Get string representation of field."""
        entry = self.ENTRIES[field]
        value = getattr(self, field)
        if entry.to_string is not None:
            value = entry.to_string(value)
        return json.dumps(value)

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
                    value = cp.get(entry.section, entry.option)
                    self.set(field, value)
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
                cp.set(entry.section, entry.option, self.get(field))

            with io.open(self._config_file, "w") as f:
                cp.write(f)
        except errors.InvalidConfiguration:
            raise
        except Exception as e:
            raise errors.InvalidConfiguration(
                operation=errors.InvalidConfiguration.Op.save, error=e
            )

    @classmethod
    def get_application_config(cls) -> "TeaConsoleConfig":
        """Finds the application config."""
        klass = cls
        while True:
            subclasses = klass.__subclasses__()
            if len(subclasses) == 0:
                return klass.instance
            elif len(subclasses) == 1:
                klass = subclasses[0]
            else:
                raise errors.InvalidConfiguration(
                    "There should be a straight line of config inheritance."
                )
