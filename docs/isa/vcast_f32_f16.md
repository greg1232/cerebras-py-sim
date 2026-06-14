# VCAST_F32_F16 (Cast FP32 to FP16)

## Description
Casts 32-bit floating point values to 16-bit.

## Behavior
```c
void execute_vcast_f32_f16(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            // In this sim, we treat data as f32, so this is a no-op/identity
            state->regs[rd].data.f32[i] = state->regs[rs1].data.f32[i];
        }
    }
}
```
