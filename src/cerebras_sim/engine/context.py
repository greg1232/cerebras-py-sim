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
