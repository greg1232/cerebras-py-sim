# LDR_DSD (Load DSD)

## Description
Loads a value from SRAM using the current DSD configuration.

## Behavior
```c
void execute_ldr_dsd(CS3CoreState *state, int rd) {
    if (state->dsd.current_ptr < state->dsd.limit && state->dsd.current_ptr < 48 * 1024) {
        state->regs[rd].data.f32[0] = (float)(*(uint32_t*)&state->sram[state->dsd.current_ptr]);
    }
}
```
