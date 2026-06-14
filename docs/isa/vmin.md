# VMIN (Vector Minimum)

## Description
Computes the element-wise minimum of two SIMD-8 vector registers.

## Behavior
```c
void execute_vmin(CS3CoreState *state, int rs1, int rs2, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            state->regs[rd].data.f32[i] = fminf(state->regs[rs1].data.f32[i], state->regs[rs2].data.f32[i]);
        }
    }
}
```
