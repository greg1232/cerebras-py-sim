# WAIT_S (Wait South) — Internal Hardware Primitive

> **Not user-accessible.** This instruction is an internal hardware primitive used by the global memory dispatch unit to implement `LDR_GLOBAL` and `STR_GLOBAL`. Kernel programmers should use `load_global` and `store_global` instead.

## Description
Stalls the hardware global memory unit until a packet arrives from the South neighbor on the NESW mesh. Invoked automatically by the hardware to synchronize southward global memory transactions.

## Behavior
```c
void execute_wait_s(CS3CoreState *state, MeshNetwork *net) {
    while (!net->has_packet(state->core_x, state->core_y, SOUTH)) {
        // Stall cycle
    }
}
```
