# LDR (Load Register)

## Description
Loads a 32-bit value from the local SRAM into the specified register's first lane.

## Behavior
```c
void execute_ldr(CS3CoreState *state, uint32_t addr, int rd) {
    if (addr >= 48 * 1024) return; // Out of bounds
    uint32_t val = *(uint32_t*)&state->sram[addr];
    state->regs[rd].data.f32[0] = (float)val;
}
```
