# STR_GLOBAL (Global Store)

## Description
Stores the value of a register into the global address space. The global address space includes the external Weight Server (DRAM) and the SRAM of any PE on the wafer.

This is the primary instruction for inter-PE communication and host-device data transfer. The hardware resolves the target address and internally uses the NESW mesh to route the store request to the appropriate PE or to the IO fabric for Weight Server access.

## Encoding (G-Type)
```
| 31      26 | 25    21 | 20      0 |
|   0x09     |    rs    |   addr24   |
```
- `Opcode` = 0x09
- `rs` (5 bits): Source register containing the value to store (0-31).
- `addr24` (24 bits): Global address offset.

## Behavior
```c
void execute_str_global(CS3CoreState *state, uint32_t global_addr, int rs, GlobalMemory *gmem) {
    // Hardware resolves global_addr to either:
    //   - Weight Server (if address is in the IO-mapped range)
    //   - Remote PE's SRAM (if address is in a PE's SRAM range)
    // The NESW mesh is used internally for PE-to-PE routing.
    float val = state->regs[rs].data.f32[0];
    gmem->store(global_addr, val);
}
```

## Latency
- Weight Server access: ~100+ cycles (IO fabric round-trip).
- Remote PE SRAM access: variable, depends on mesh hop distance (~1 cycle/hop).

## Usage Notes
- Stores are asynchronous; a `sync()` is typically needed to ensure all PEs have completed their stores before dependents attempt to load.
- This instruction replaces the explicit `SEND_*` primitive for all inter-block and host-device data movement.
- Within the same block, the hardware may optimize routing to use direct mesh links.
