import typer
from rich import print

from tea import serde
from tea_console.console import command
from tea_console.config import ConfigEntry
from tea_console.config import TeaConsoleConfig
from tea_console.engine.config_engine import ConfigEngine


app = typer.Typer(name="config", help="Configuration set/get.")


@command(app, model=ConfigEntry, name="list")
def list_values():
    """List all configuration values."""
    config = TeaConsoleConfig.get_application_config()
    if config.format == config.Format.text:
        for i, (key, entries) in enumerate(ConfigEngine.list().items()):
            if i > 0:
                print()
            print(f"[cyan]\\[{key}][/cyan]")
            for entry in entries:
                print(f"[green]{entry.key}[/green]: {entry.value}")

    elif config.format == config.Format.json:
        print(serde.json_dumps(ConfigEngine.list()))


@command(app, model=ConfigEntry, name="set")
def set_value(key: str, value: str):
    """Set a configuration key."""
    ConfigEngine.set(key=key, value=value)
    list_values()
