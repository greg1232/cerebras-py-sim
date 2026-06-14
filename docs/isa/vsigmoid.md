# VSIGMOID (Vector Sigmoid)

## Description
Applies a sigmoid approximation to each lane of the SIMD-8 register.

## Behavior
```c
void execute_vsigmoid(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            float x = state->regs[rs1].data.f32[i];
            state->regs[rd].data.f32[i] = 1.0f / (1.0f + expf(-x));
        }
    }
}
```
