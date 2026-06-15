# SEND_N (Send North) — Internal Hardware Primitive

> **Not user-accessible.** This instruction is an internal hardware primitive used by the global memory dispatch unit to implement `LDR_GLOBAL` and `STR_GLOBAL`. Kernel programmers should use `load_global` and `store_global` instead.

## Description
Sends the content of a register to the North neighbor core via the NESW mesh. This primitive is invoked automatically by the hardware when a global memory operation requires northward routing.

## Behavior
```c
void execute_send_n(CS3CoreState *state, int rs1, MeshNetwork *net) {
    MeshPacket pkt;
    pkt.payload = (uint16_t)state->regs[rs1].data.f32[0]; // Simplified: send first lane
    pkt.source_dir = 0; // North
    pkt.flags = 0;
    net->send_packet(state->core_x, state->core_y, NORTH, pkt);
}
```
