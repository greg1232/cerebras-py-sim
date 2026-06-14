# VCLIP (Vector Clip)

## Description
Clamps each lane of the SIMD-8 register to a specified range [min, max].

## Behavior
```c
void execute_vclip(CS3CoreState *state, int rs1, int rs_min, int rs_max, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            float val = state->regs[rs1].data.f32[i];
            float min_val = state->regs[rs_min].data.f32[0];
            float max_val = state->regs[rs_max].data.f32[0];
            state->regs[rd].data.f32[i] = (val < min_val) ? min_val : (val > max_val ? max_val : val);
        }
    }
}
```
