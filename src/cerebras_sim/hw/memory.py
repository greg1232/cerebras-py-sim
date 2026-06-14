import numpy as np
from typing import Dict, Optional

class DevicePtr:
    """64-bit opaque device address."""
    __slots__ = ("address",)

    def __init__(self, address: int):
        self.address = address

    def __int__(self):
        return self.address

    def __repr__(self):
        return f"DevicePtr(0x{self.address:016x})"

    def __eq__(self, other):
        if isinstance(other, DevicePtr):
            return self.address == other.address
        if isinstance(other, int):
            return self.address == other
        return False

    def __hash__(self):
        return hash(self.address)

class WeightServer:
    """
    Simulates external DRAM (Weight Server) with up to 1.5TB of addressable memory.
    Uses a dictionary-based pool to avoid pre-allocating massive buffers.
    """
    MAX_MEMORY = 1.5 * 1024 * 1024 * 1024 * 1024  # 1.5 TB

    def __init__(self):
        self._pool: Dict[int, bytearray] = {}
        self._next_address = 0x100000000  # Start above 4GB to avoid common low-addr collisions
        self._allocated_bytes = 0
        self.total_bytes_transferred = 0

    def malloc(self, size: int) -> Optional[DevicePtr]:
        """Allocate a region and return a DevicePtr."""
        if self._allocated_bytes + size > self.MAX_MEMORY:
            return None

        ptr = DevicePtr(self._next_address)
        self._pool[ptr.address] = bytearray(size)

        self._next_address += size
        self._allocated_bytes += size
        return ptr

    def free(self, ptr: DevicePtr):
        """Return a region to the pool."""
        if ptr.address not in self._pool:
            raise ValueError(f"Invalid DevicePtr: {ptr}")

        size = len(self._pool[ptr.address])
        del self._pool[ptr.address]
        self._allocated_bytes -= size

    def memcpy_h2d(self, dst: DevicePtr, src: bytes | bytearray | np.ndarray):
        """Copy bytes from host (Python/Numpy) into the WeightServer."""
        if dst.address not in self._pool:
            raise ValueError(f"Invalid DevicePtr: {dst}")

        # Convert src to bytes
        if isinstance(src, np.ndarray):
            src_bytes = src.tobytes()
        elif isinstance(src, (bytes, bytearray)):
            src_bytes = src
        else:
            src_bytes = bytes(src)

        size = len(src_bytes)
        if size > len(self._pool[dst.address]):
            raise ValueError("Source size exceeds allocated device memory block size")

        self._pool[dst.address][:size] = src_bytes
        self.total_bytes_transferred += size

    def memcpy_d2h(self, src: DevicePtr, size: int) -> bytearray:
        """Copy bytes from WeightServer into a Python bytearray."""
        if src.address not in self._pool:
            raise ValueError(f"Invalid DevicePtr: {src}")

        if size > len(self._pool[src.address]):
            raise ValueError("Requested size exceeds allocated device memory block size")

        data = self._pool[src.address][:size]
        self.total_bytes_transferred += size
        return bytearray(data)

    def load(self, ptr: DevicePtr, offset: int = 0) -> float:
        """Read a single float32 from device memory."""
        if ptr.address not in self._pool:
            raise ValueError(f"Invalid DevicePtr: {ptr}")

        buf = self._pool[ptr.address]
        if offset + 4 > len(buf):
            raise IndexError("Offset out of bounds for device memory block")

        # Use numpy to interpret bytes as float32
        val = np.frombuffer(buf[offset : offset + 4], dtype=np.float32)[0]
        return float(val)

    def store(self, ptr: DevicePtr, offset: int, val: float):
        """Write a single float32 to device memory."""
        if ptr.address not in self._pool:
            raise ValueError(f"Invalid DevicePtr: {ptr}")

        buf = self._pool[ptr.address]
        if offset + 4 > len(buf):
            raise IndexError("Offset out of bounds for device memory block")

        # Convert float to bytes
        val_bytes = np.array([val], dtype=np.float32).tobytes()
        buf[offset : offset + 4] = val_bytes
