# NEXT_DSD (Next DSD)

## Description
Advances the DSD current pointer by the configured stride.

## Behavior
```c
void execute_next_dsd(CS3CoreState *state) {
    state->dsd.current_ptr += state->dsd.stride;
}
```
