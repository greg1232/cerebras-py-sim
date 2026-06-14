# VTANH (Vector Tanh)

## Description
Computes the hyperbolic tangent of each lane in the SIMD-8 register.

## Behavior
```c
void execute_vtanh(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            state->regs[rd].data.f32[i] = tanhf(state->regs[rs1].data.f32[i]);
        }
    }
}
```
