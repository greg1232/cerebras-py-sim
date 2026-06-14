# VRELU (Vector ReLU)

## Description
Applies the Rectified Linear Unit function (`max(0, x)`) to each lane of the SIMD-8 register.

## Behavior
```c
void execute_vrelu(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            float val = state->regs[rs1].data.f32[i];
            state->regs[rd].data.f32[i] = (val > 0.0f) ? val : 0.0f;
        }
    }
}
```
