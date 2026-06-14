# STR_DSD (Store DSD)

## Description
Stores a value to SRAM using the current DSD configuration.

## Behavior
```c
void execute_str_dsd(CS3CoreState *state, int rs1) {
    if (state->dsd.current_ptr < state->dsd.limit && state->dsd.current_ptr < 48 * 1024) {
        uint32_t val = (uint32_t)state->regs[rs1].data.f32[0];
        *(uint32_t*)&state->sram[state->dsd.current_ptr] = val;
    }
}
```
