# VCAST_F16_F32 (Cast FP16 to FP32)

## Description
Casts 16-bit floating point values to 32-bit.

## Behavior
```c
void execute_vcast_f16_f32(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            // In this sim, we treat data as f32, so this is a no-op/identity
            state->regs[rd].data.f32[i] = state->regs[rs1].data.f32[i];
        }
    }
}
```
