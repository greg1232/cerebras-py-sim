# VSQRT (Vector Square Root)

## Description
Computes the square root of each lane in the SIMD-8 register.

## Behavior
```c
void execute_vsqrt(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            state->regs[rd].data.f32[i] = sqrtf(state->regs[rs1].data.f32[i]);
        }
    }
}
```
