# SEND_N (Send North)

## Description
Sends the content of a register to the North neighbor core.

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
