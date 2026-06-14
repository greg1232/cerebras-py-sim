# VGELU (Vector GELU)

## Description
Applies the Gaussian Error Linear Unit approximation to each lane of the SIMD-8 register.

## Behavior
```c
void execute_vgelu(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            float x = state->regs[rs1].data.f32[i];
            // Simplified GELU approximation: 0.5x(1 + tanh(sqrt(2/pi)(x + 0.044715x^3)))
            state->regs[rd].data.f32[i] = 0.5f * x * (1.0f + tanhf(0.7978845608f * (x + 0.044715f * x * x * x)));
        }
    }
}
```
