# GET_TICK (Get Cycle Counter)

## Description
Reads the local core's cycle counter (`tick_counter`) into the first lane of a destination register. The counter is a free-running 64-bit cycle count, so reading it before and after a region of code yields the elapsed cycles. Useful for profiling and timing loops. Combine with the current `clock_freq` to convert cycles into wall-clock time.

## Behavior
```c
void execute_get_tick(CS3CoreState *state, int rd) {
    // Low 32 bits of the cycle counter land in lane 0.
    state->regs[rd].data.i32[0] = (uint32_t)(state->tick_counter & 0xFFFFFFFF);
}
```
