# VMASK (Set Vector Mask)

## Description
Sets the 8-bit lane mask register. Each bit controls whether the corresponding SIMD lane participates in subsequent vector operations. A bit value of 1 means the lane is active.

## Behavior
```c
void execute_vmask(CS3CoreState *state, uint8_t mask_value) {
    state->mask = mask_value & 0xFF; // Only low 8 bits valid
}
```
