# SET_DSD (Set DSD)

## Description
Configures the Data Structure Descriptor for indirect memory access.

## Behavior
```c
void execute_set_dsd(CS3CoreState *state, uint32_t base, uint32_t stride, uint32_t limit) {
    state->dsd.base_addr = base;
    state->dsd.stride = stride;
    state->dsd.limit = limit;
    state->dsd.current_ptr = base;
}
```
