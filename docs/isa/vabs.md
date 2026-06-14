# VABS (Vector Absolute Value)

## Description
Computes the absolute value of each lane in the specified SIMD-8 vector register.

## Behavior
```c
void execute_vabs(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            state->regs[rd].data.f32[i] = fabsf(state->regs[rs1].data.f32[i]);
        }
    }
}
```
