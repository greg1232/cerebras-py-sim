from collections import deque
from dataclasses import dataclass
from enum import auto, Enum
from typing import Any


class CommandType(Enum):
    MALLOC = auto()
    FREE = auto()
    MEMCPY_H2D = auto()
    MEMCPY_D2H = auto()
    KERNEL_LAUNCH = auto()
    SYNC_BARRIER = auto()


@dataclass
class Command:
    type: CommandType
    args: dict[str, Any]


class CS3Queue:
    """A FIFO command queue for host-to-device submissions."""

    def __init__(self):
        self._commands: deque[Command] = deque()

    def enqueue(self, cmd_type: CommandType, **kwargs):
        """Push a Command of the given type with arbitrary keyword args."""
        self._commands.append(Command(type=cmd_type, args=dict(kwargs)))

    def drain(self) -> list[Command]:
        """Pop all queued commands (FIFO order) and return them."""
        drained = list(self._commands)
        self._commands.clear()
        return drained
