# VLOG (Vector Logarithm)

## Description
Computes the natural logarithm ($\ln x$) of each lane in the SIMD-8 register.

## Behavior
```c
void execute_vlog(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            state->regs[rd].data.f32[i] = logf(state->regs[rs1].data.f32[i]);
        }
    }
}
```
