# VADD (Vector Addition)

## Description
Performs element-wise addition of two SIMD-8 vector registers. Only lanes enabled in the current `mask` are updated.

## Behavior
```c
void execute_vadd(CS3CoreState *state, int rs1, int rs2, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            state->regs[rd].data.f32[i] = state->regs[rs1].data.f32[i] + state->regs[rs2].data.f32[i];
        }
    }
}
```
