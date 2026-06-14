# SYNC Instruction

The `SYNC` instruction acts as a synchronization barrier for the core. When a core executes `SYNC`, it enters a wait state and cannot proceed to the next instruction until all of its immediate neighbors in the mesh (North, South, East, and West) have also reached their own `SYNC` point.

Once all neighboring cores have checked in, the barrier is released, and all participating cores may continue execution.

## C Implementation Behavior

```c
void execute_sync(CS3CoreState *state, MeshNetwork *net) {
    // Signal to neighbors that this core has reached the SYNC point
    // and wait until all neighbors signal back.
    while (!net->all_neighbors_synced(state->core_x, state->core_y)) {
        // Core spins/waits until the mesh network confirms 
        // N, S, E, and W neighbors have reached their barrier.
        cpu_relax(); 
    }
}
```
