from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Kernel:
    """A compiled CS3 kernel: a Python function plus its PE block dimensions."""

    name: str
    func: Callable
    block_w: int
    block_h: int

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


@dataclass
class KernelArgs:
    """Arguments (DevicePtrs and scalars) broadcast to every PE in a launch."""

    args: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.args[key]

    def __setitem__(self, key: str, value: Any):
        self.args[key] = value


def cs3_kernel(_func=None, *, block_w: int = 1, block_h: int = 1):
    """Mark a Python function as a CS3 kernel.

    Usable bare (``@cs3_kernel``) or with block dimensions
    (``@cs3_kernel(block_w=16, block_h=16)``). Returns a Kernel.
    """

    def wrap(func: Callable) -> Kernel:
        return Kernel(name=func.__name__, func=func, block_w=block_w, block_h=block_h)

    if _func is not None:
        return wrap(_func)
    return wrap
