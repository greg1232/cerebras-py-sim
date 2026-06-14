# VCAST_I8_F16 (Cast INT8 to FP16)

## Description
Casts 8-bit signed integers to floating point.

## Behavior
```c
void execute_vcast_i8_f16(CS3CoreState *state, int rs1, int rd) {
    for (int i = 0; i < 8; i++) {
        if ((state->mask >> i) & 1) {
            state->regs[rd].data.f32[i] = (float)state->regs[rs1].data.i8[i];
        }
    }
}
```
