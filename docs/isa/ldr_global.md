# LDR_GLOBAL (Global Load)

## Description
Loads a value from the global address space into a register. The global address space includes the external Weight Server (DRAM) and the SRAM of any PE on the wafer.

This is the primary instruction for inter-PE communication and host-device data transfer. The hardware resolves the target address and internally uses the NESW mesh to route the load request to the appropriate PE or to the IO fabric for Weight Server access.

## Encoding (G-Type)
```
| 31      26 | 25    21 | 20      0 |
|   0x08     |    rd    |   addr24   |
```
- `Opcode` = 0x08
- `rd` (5 bits): Destination register (0-31).
- `addr24` (24 bits): Global address offset.

## Behavior
```c
void execute_ldr_global(CS3CoreState *state, uint32_t global_addr, int rd, GlobalMemory *gmem) {
    // Hardware resolves global_addr to either:
    //   - Weight Server (if address is in the IO-mapped range)
    //   - Remote PE's SRAM (if address is in a PE's SRAM range)
    // The NESW mesh is used internally for PE-to-PE routing.
    float val = gmem->load(global_addr);
    state->regs[rd].data.f32[0] = val;
}
```

## Latency
- Weight Server access: ~100+ cycles (IO fabric round-trip).
- Remote PE SRAM access: variable, depends on mesh hop distance (~1 cycle/hop).

## Usage Notes
- Prefetching into `__local` SRAM is strongly recommended to hide load latency.
- This instruction replaces the explicit `RECV_*` primitive for all inter-block and host-device data movement.
- Within the same block, the hardware may optimize routing to use direct mesh links.
