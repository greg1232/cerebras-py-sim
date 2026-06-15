from ..hw.memory import WeightServer, DevicePtr
from ..engine.perf_model import PerformanceCounter


class KernelContext:
    """
    Per-PE execution context provided to kernel functions.
    Exposes the DSL API: pe_x/pe_y, load_global/store_global.
    Automatically tracks instruction latency through the shared perf counter.
    """

    def __init__(self, x: int, y: int, weight_server: WeightServer, perf: PerformanceCounter, sampler: Any):
        self._x = x
        self._y = y
        self._ws = weight_server
        self._perf = perf
        self._sampler = sampler

    def pe_x(self) -> int:
        return self._x

    def pe_y(self) -> int:
        return self._y

    def load_global(self, ptr: DevicePtr, byte_offset: int) -> float:
        """Load a float32 from weight server at ptr+byte_offset. Tracks LDR_GLOBAL latency."""
        self._perf.add_instruction_latency("LDR_GLOBAL")
        if not self._sampler.is_pe_sampled(self._x, self._y):
            return 0.0
        return self._ws.load(ptr, byte_offset)

    def store_global(self, ptr: DevicePtr, byte_offset: int, val: float):
        """Store a float32 to weight server at ptr+byte_offset. Tracks STR_GLOBAL latency."""
        self._perf.add_instruction_latency("STR_GLOBAL")
        if not self._sampler.is_pe_sampled(self._x, self._y):
            return
        self._ws.store(ptr, byte_offset, val)

    def sram_alloc(self, name: str, size: int):
        """Allocate a tile in local SRAM. Tracks SRAM_ALLOC latency."""
        self._perf.add_instruction_latency("SRAM_ALLOC")
        # In the functional simulation, we return a handle (name) to the buffer
        return {"name": name, "size": size}

    def sram_load(self, handle: dict, offset: int) -> float:
        """Load from local SRAM. Tracks LDR latency."""
        self._perf.add_instruction_latency("LDR")
        return 0.0 # Functional value determined by simulation state

    def sram_store(self, handle: dict, offset: int, val: float):
        """Store to local SRAM. Tracks STR latency."""
        self._perf.add_instruction_latency("STR")

    def shift_right(self, handle: dict, offset: int) -> float:
        """Pull from East neighbor SRAM. Tracks MESH_SHIFT latency."""
        self._perf.add_instruction_latency("MESH_SHIFT")
        return 0.0

    def shift_down(self, handle: dict, offset: int) -> float:
        """Pull from South neighbor SRAM. Tracks MESH_SHIFT latency."""
        self._perf.add_instruction_latency("MESH_SHIFT")
        return 0.0

    def neighbor_load(self, handle: dict, direction: str, offset: int) -> float:
        """Read from neighbor SRAM. Tracks MESH_READ latency."""
        self._perf.add_instruction_latency("MESH_READ")
        return 0.0

    def sync(self):
        """Global BSP Synchronization. Tracks SYNC latency."""
        self._perf.add_instruction_latency("SYNC")

