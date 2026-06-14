# HALT Instruction

The `HALT` instruction puts the core into a low-power wait state. Upon execution, the core sets its `halted` flag to true and ceases all instruction fetching and execution.

The core will remain in this state indefinitely until an external wake signal (such as an interrupt or a system-level reset) is received, at which point `halted` is set to false and the core resumes execution from the current program counter.

## C Implementation Behavior

```c
void execute_halt(CS3CoreState *state) {
    // Put the core into a low-power wait state
    state->halted = true;
}
```
