# B_JMP (Unconditional Jump)

## Description
Unconditionally jumps to the specified PC address.

## Behavior
```c
void execute_b_jmp(CS3CoreState *state, uint32_t target_pc) {
    state->pc = target_pc;
}
```
