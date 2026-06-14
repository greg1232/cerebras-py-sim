# POLL_MESH (Poll Mesh)

## Description
Non-blocking check to see if any packets are pending in the local core's mesh buffers.

## Behavior
```c
void execute_poll_mesh(CS3CoreState *state, int rd, MeshNetwork *net) {
    bool data_available = net->has_any_packet(state->core_x, state->core_y);
    state->regs[rd].data.i32[0] = data_available ? 1 : 0;
}
```
