# SMI_READ (System Management Interface Read)

## Description
Reads the core's system management / telemetry status register into the first lane of the destination register `rd`. The `smi_status` register is a packed snapshot of on-core telemetry: temperature, error flags, and power state. The value is written only to lane 0 of `rd`; the remaining lanes are left untouched. This instruction is non-destructive and does not clear or modify `smi_status`.

## Behavior
```c
void execute_smi_read(CS3CoreState *state, int rd) {
    // smi_status packs telemetry/status fields, e.g.:
    //   bits  [7:0]  temperature (degrees C)
    //   bits [15:8]  error flags
    //   bits [17:16] power state
    state->regs[rd].data.i32[0] = state->smi_status;
}
```
