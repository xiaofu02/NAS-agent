# tools/base.py

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[..., Any]
    category: str = "general"
    command: str = ""
    aliases: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    show_in_help: bool = True
    formatter: Callable[[dict], None] | None = None
    arg_mode: str = "none"   # none / text_tail