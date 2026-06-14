# VEXP (Vector Exponential)

## Description
Computes the exponential ($e^x$) of each lane in the SIMD-8 register.

## Behavior
```c
void execute_vexp(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            state->regs[rd].data.f32[i] = expf(state->regs[rs1].data.f32[i]);
        }
    }
}
```
