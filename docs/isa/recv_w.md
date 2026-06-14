# RECV_W (Receive West)

## Description
Receives a packet from the West neighbor and stores it in the specified register.

## Behavior
```c
void execute_recv_w(CS3CoreState *state, int rd, MeshNetwork *net) {
    MeshPacket pkt = net->pop_packet(state->core_x, state->core_y, WEST);
    state->regs[rd].data.f32[0] = (float)pkt.payload;
}
```
