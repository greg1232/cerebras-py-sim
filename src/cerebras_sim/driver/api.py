from ..hw.memory import WeightServer, DevicePtr
from .queue import CS3Queue, CommandType


class CS3Driver:
    """Host-side cs3_* API that backs requests onto a WeightServer and command queue."""

    def __init__(self):
        self.weight_server = WeightServer()
        self.queue = CS3Queue()

    def cs3_malloc(self, size: int) -> DevicePtr:
        """Allocate device memory and record the allocation on the queue."""
        ptr = self.weight_server.malloc(size)
        if ptr is None:
            raise MemoryError(f"cs3_malloc failed: out of device memory ({size} bytes)")
        self.queue.enqueue(CommandType.MALLOC, ptr=ptr, size=size)
        return ptr

    def cs3_free(self, ptr: DevicePtr):
        """Enqueue a free of the given device pointer."""
        self.queue.enqueue(CommandType.FREE, ptr=ptr)

    def cs3_memcpy_h2d(self, dst: DevicePtr, src, size: int):
        """Enqueue a host-to-device copy."""
        self.queue.enqueue(CommandType.MEMCPY_H2D, dst=dst, src=src, size=size)

    def cs3_memcpy_d2h(self, src: DevicePtr, size: int) -> bytearray:
        """Enqueue a device-to-host copy and return a destination buffer."""
        dst = bytearray(size)
        self.queue.enqueue(CommandType.MEMCPY_D2H, src=src, dst=dst, size=size)
        return dst

    def cs3_launch(self, kernel, grid_w, grid_h, block_w, block_h, args: dict):
        """Enqueue a kernel launch over a grid of blocks."""
        self.queue.enqueue(
            CommandType.KERNEL_LAUNCH,
            kernel=kernel,
            grid_w=grid_w,
            grid_h=grid_h,
            block_w=block_w,
            block_h=block_h,
            args=args,
        )

    def cs3_sync(self):
        """Enqueue a synchronization barrier."""
        self.queue.enqueue(CommandType.SYNC_BARRIER)
