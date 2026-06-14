# B_COND (Conditional Branch)

## Description
Branches to a target PC if the first lane of a given register is non-zero. Used for conditional control flow.

## Behavior
```c
void execute_b_cond(CS3CoreState *state, int rs1, uint32_t target_pc) {
    if (state->regs[rs1].data.i32[0] != 0) {
        state->pc = target_pc;
    }
}
```
