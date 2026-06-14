# WAIT_N (Wait North)

## Description
Stalls the core until a packet arrives from the North neighbor.

## Behavior
```c
void execute_wait_n(CS3CoreState *state, MeshNetwork *net) {
    while (!net->has_packet(state->core_x, state->core_y, NORTH)) {
        // Stall cycle
    }
}
```
