import enum
from dataclasses import dataclass
from typing import List, Union, Callable, Any

from rich.table import Table


class Align(str, enum.Enum):
    left = "left"
    center = "center"
    right = "right"


@dataclass
class Column:
    Align = Align

    title: str
    path: Union[str, Callable[[Any], str]]
    align: str = Align.left


def _get_path(obj, path) -> str:
    if callable(path):
        obj = path(obj)
    else:
        path = path.split(".")
        for item in path:
            obj = getattr(obj, item)
        if isinstance(obj, bool):
            obj = ":white_check_mark:" if obj else ":cross_mark:"
    return f"{obj}"


class RichTableMixin:
    HEADERS: List[Column] = []

    @classmethod
    def get_rich_table(cls, header_style="bold magenta") -> Table:
        table = Table(show_header=True, header_style=header_style)
        for column in cls.HEADERS:
            table.add_column(header=column.title, justify=column.align)
        return table

    def to_rich_row(self) -> list:
        return [_get_path(self, column.path) for column in self.HEADERS]
