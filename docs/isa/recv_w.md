# RECV_W (Receive West) — Internal Hardware Primitive

> **Not user-accessible.** This instruction is an internal hardware primitive used by the global memory dispatch unit to implement `LDR_GLOBAL` and `STR_GLOBAL`. Kernel programmers should use `load_global` and `store_global` instead.

## Description
Receives a packet from the West neighbor via the NESW mesh and stores it in the specified register. Invoked automatically by the hardware to complete a westward global memory transaction.

## Behavior
```c
void execute_recv_w(CS3CoreState *state, int rd, MeshNetwork *net) {
    MeshPacket pkt = net->pop_packet(state->core_x, state->core_y, WEST);
    state->regs[rd].data.f32[0] = (float)pkt.payload;
}
```
