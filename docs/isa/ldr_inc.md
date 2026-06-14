# LDR_INC (Load and Increment)

## Description
Loads a value from SRAM and automatically increments the address pointer.

## Behavior
```c
void execute_ldr_inc(CS3CoreState *state, uint32_t *ptr, int rd) {
    uint32_t addr = *ptr;
    if (addr < 48 * 1024) {
        state->regs[rd].data.f32[0] = (float)(*(uint32_t*)&state->sram[addr]);
        *ptr += 4;
    }
}
```
