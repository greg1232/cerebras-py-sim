# STR (Store Register)

## Description
Stores the value of a register's first lane into the local SRAM.

## Behavior
```c
void execute_str(CS3CoreState *state, uint32_t addr, int rs1) {
    if (addr >= 48 * 1024) return; // Out of bounds
    uint32_t val = (uint32_t)state->regs[rs1].data.f32[0];
    *(uint32_t*)&state->sram[addr] = val;
}
```
