# WAIT_S (Wait South)

## Description
Stalls the core until a packet arrives from the South neighbor.

## Behavior
```c
void execute_wait_s(CS3CoreState *state, MeshNetwork *net) {
    while (!net->has_packet(state->core_x, state->core_y, SOUTH)) {
        // Stall cycle
    }
}
```
