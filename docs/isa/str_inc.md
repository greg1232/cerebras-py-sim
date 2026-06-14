# STR_INC (Store and Increment)

## Description
Stores a value to SRAM and automatically increments the address pointer.

## Behavior
```c
void execute_str_inc(CS3CoreState *state, uint32_t *ptr, int rs1) {
    uint32_t addr = *ptr;
    if (addr < 48 * 1024) {
        uint32_t val = (uint32_t)state->regs[rs1].data.f32[0];
        *(uint32_t*)&state->sram[addr] = val;
        *ptr += 4;
    }
}
```
