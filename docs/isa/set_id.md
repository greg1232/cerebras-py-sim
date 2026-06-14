# SET_ID (Set Core Identity)

## Description
Programs the core's (X, Y) mesh coordinates from two source registers. During boot/configuration each core executes SET_ID to assign itself a unique identity within the 800x900 grid. The X coordinate is taken from the first lane of source register `rs_x` and the Y coordinate from the first lane of `rs_y`. Values are truncated to 16 bits and clamped to the valid mesh extent (X in [0, 799], Y in [0, 899]).

## Behavior
```c
void execute_set_id(CS3CoreState *state, int rs_x, int rs_y) {
    uint32_t x = state->regs[rs_x].data.i32[0];
    uint32_t y = state->regs[rs_y].data.i32[0];

    // Clamp to the 800x900 mesh extent.
    if (x >= 800) x = 799;
    if (y >= 900) y = 899;

    state->core_x = (uint16_t)x;
    state->core_y = (uint16_t)y;
}
```
