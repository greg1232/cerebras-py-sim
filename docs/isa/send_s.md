# SEND_S (Send South)

## Description
Sends the content of a register to the South neighbor core.

## Behavior
```c
void execute_send_s(CS3CoreState *state, int rs1, MeshNetwork *net) {
    MeshPacket pkt;
    pkt.payload = (uint16_t)state->regs[rs1].data.f32[0];
    pkt.source_dir = 1; // South
    pkt.flags = 0;
    net->send_packet(state->core_x, state->core_y, SOUTH, pkt);
}
```
