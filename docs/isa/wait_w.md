# WAIT_W (Wait West)

## Description
Stalls the core until a packet arrives from the West neighbor.

## Behavior
```c
void execute_wait_w(CS3CoreState *state, MeshNetwork *net) {
    while (!net->has_packet(state->core_x, state->core_y, WEST)) {
        // Stall cycle
    }
}
```
