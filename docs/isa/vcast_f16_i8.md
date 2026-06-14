# VCAST_F16_I8 (Cast FP16 to INT8)

## Description
Casts floating point values to 8-bit signed integers with saturation.

## Behavior
```c
void execute_vcast_f16_i8(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            float val = state->regs[rs1].data.f32[i];
            if (val > 127.0f) val = 127.0f;
            if (val < -128.0f) val = -128.0f;
            state->regs[rd].data.i8[i] = (int8_t)val;
        }
    }
}
```
