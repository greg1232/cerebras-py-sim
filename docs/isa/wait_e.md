# WAIT_E (Wait East)

## Description
Stalls the core until a packet arrives from the East neighbor.

## Behavior
```c
void execute_wait_e(CS3CoreState *state, MeshNetwork *net) {
    while (!net->has_packet(state->core_x, state->core_y, EAST)) {
        // Stall cycle
    }
}
```
