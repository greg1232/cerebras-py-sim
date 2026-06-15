# CS3 Simulator ISA Reference

Index of all instructions supported by the CS3 simulator, grouped by category.
Each entry links to its detailed specification.

## Compute (SIMD-8 Arithmetic)

- [vadd](vadd.md) — Element-wise addition of two SIMD-8 vector registers.
- [vsub](vsub.md) — Element-wise subtraction of two SIMD-8 vector registers.
- [vmul](vmul.md) — Element-wise multiplication of two SIMD-8 vector registers.
- [vdiv](vdiv.md) — Element-wise division of two SIMD-8 vector registers (divide-by-zero yields 0).
- [vfmadd](vfmadd.md) — Fused multiply-add: `C = A * B + C` per lane.
- [vabs](vabs.md) — Absolute value of each lane.
- [vmax](vmax.md) — Element-wise maximum of two SIMD-8 vector registers.
- [vmin](vmin.md) — Element-wise minimum of two SIMD-8 vector registers.
- [vneg](vneg.md) — Negates each lane.

## Activations & Special Functions

- [vrelu](vrelu.md) — Applies ReLU (`max(0, x)`) to each lane.
- [vgelu](vgelu.md) — Applies the GELU (tanh) approximation to each lane.
- [vsigmoid](vsigmoid.md) — Applies the sigmoid function to each lane.
- [vtanh](vtanh.md) — Hyperbolic tangent of each lane.
- [vexp](vexp.md) — Exponential (`e^x`) of each lane.
- [vlog](vlog.md) — Natural logarithm (`ln x`) of each lane.
- [vsqrt](vsqrt.md) — Square root of each lane.

## Casting & Quantization

- [vcast_f16_f32](vcast_f16_f32.md) — Casts FP16 values to FP32.
- [vcast_f32_f16](vcast_f32_f16.md) — Casts FP32 values to FP16.
- [vcast_i8_f16](vcast_i8_f16.md) — Casts INT8 values to floating point.
- [vcast_f16_i8](vcast_f16_i8.md) — Casts floating point to INT8 with saturation.
- [vclip](vclip.md) — Clamps each lane to a `[min, max]` range.

## Global Memory

- [ldr_global](ldr_global.md) — Loads a value from the global address space (Weight Server or remote PE SRAM) into a register.
- [str_global](str_global.md) — Stores a register's value to the global address space (Weight Server or remote PE SRAM).

## Internal Hardware Primitives (Mesh — Not User-Accessible)

> The following instructions are used internally by the hardware to implement `LDR_GLOBAL` and `STR_GLOBAL`. They are not available to kernel programmers and should not be emitted by the compiler.

- [send_n](send_n.md) — Internal: sends a register's value to the North neighbor core.
- [send_s](send_s.md) — Internal: sends a register's value to the South neighbor core.
- [send_e](send_e.md) — Internal: sends a register's value to the East neighbor core.
- [send_w](send_w.md) — Internal: sends a register's value to the West neighbor core.
- [recv_n](recv_n.md) — Internal: receives a packet from the North neighbor into a register.
- [recv_s](recv_s.md) — Internal: receives a packet from the South neighbor into a register.
- [recv_e](recv_e.md) — Internal: receives a packet from the East neighbor into a register.
- [recv_w](recv_w.md) — Internal: receives a packet from the West neighbor into a register.
- [wait_n](wait_n.md) — Internal: stalls until a packet arrives from the North neighbor.
- [wait_s](wait_s.md) — Internal: stalls until a packet arrives from the South neighbor.
- [wait_e](wait_e.md) — Internal: stalls until a packet arrives from the East neighbor.
- [wait_w](wait_w.md) — Internal: stalls until a packet arrives from the West neighbor.
- [poll_mesh](poll_mesh.md) — Internal: non-blocking check for any pending packets in local mesh buffers.

## Memory (SRAM)

- [ldr](ldr.md) — Loads a 32-bit value from local SRAM into a register's first lane.
- [str](str.md) — Stores a register's first lane into local SRAM.
- [ldr_inc](ldr_inc.md) — Loads from SRAM and auto-increments the address pointer.
- [str_inc](str_inc.md) — Stores to SRAM and auto-increments the address pointer.

## DSD (Data Structure Descriptor)

- [set_dsd](set_dsd.md) — Configures the Data Structure Descriptor for indirect access.
- [ldr_dsd](ldr_dsd.md) — Loads from SRAM using the current DSD configuration.
- [str_dsd](str_dsd.md) — Stores to SRAM using the current DSD configuration.
- [next_dsd](next_dsd.md) — Advances the DSD pointer by the configured stride.

## Control Flow

- [vmask](vmask.md) — Sets the 8-bit lane mask controlling active SIMD lanes.
- [b_cond](b_cond.md) — Conditional branch taken when a register's first lane is non-zero.
- [b_jmp](b_jmp.md) — Unconditional jump to a target PC.
- [sync](sync.md) — Barrier that waits until all mesh neighbors reach their SYNC point.
- [halt](halt.md) — Puts the core into a low-power wait state until an external wake signal.

## System

- [set_clk](set_clk.md) — Sets the core clock frequency to one of four discrete levels.
- [get_tick](get_tick.md) — Reads the local cycle counter into a register's first lane.
- [set_id](set_id.md) — Programs the core's (X, Y) mesh coordinates.
- [smi_read](smi_read.md) — Reads the system management/telemetry status register.

## State Definitions

- [machine_state.c](machine_state.c) — Core architectural state structs.
- [mesh_network_state.c](mesh_network_state.c) — Mesh interconnect structs and function prototypes.
