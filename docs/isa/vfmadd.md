# VFMADD (Vector Fused Multiply-Add)

## Description
Performs the operation `C = A * B + C` for each lane of the SIMD-8 registers. Only lanes enabled in the current `mask` are updated.

## Behavior
```c
void execute_vfmadd(CS3CoreState *state, int rs1, int rs2, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            state->regs[rd].data.f32[i] = (state->regs[rs1].data.f32[i] * state->regs[rs2].data.f32[i]) + state->regs[rd].data.f32[i];
        }
    }
}
```
