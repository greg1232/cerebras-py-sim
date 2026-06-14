# cerebras-py-sim

A simulator for the Cerebras CS3 Wafer-Scale Engine. The goal is to model the CS3's massive 2D mesh of processing elements, per-core SRAM, SIMD execution units, and bidirectional mesh interconnect — enabling ISA-level program development and performance analysis without access to real hardware.

## Hardware Target

| Parameter | Value |
|-----------|-------|
| Core array | 800 x 900 (720,000 cores) |
| Per-core SRAM | 48 KB |
| SIMD width | 8 lanes |
| Clock | 750 / 850 MHz base, 1.2 / 1.4 GHz boost |
| Mesh interconnect | 16-bit bidirectional per cycle (N/S/E/W) |
| Off-chip IO | 12 x 100 Gbps links |
| External memory | Weight server via IO fabric |

## Project Status

Currently in the documentation and ISA specification phase. The full instruction set, machine state, and mesh interconnect structs are defined. Simulator implementation is next.

## Directory Structure

```
docs/
  overview.md            — Project goals and hardware specs
  isa.md                 — ISA overview and execution model
  isa_instructions.md    — Full instruction listing by category
  tungsten.md            — Tungsten dataflow domain translation language
  isa/
    README.md            — Indexed instruction reference
    encoding.md          — 32-bit binary encoding specification
    machine_state.c      — Authoritative C structs for per-core state
    mesh_network_state.c — Authoritative C structs for mesh fabric state
    <instruction>.md     — One doc per instruction (54 total)
```

## ISA Summary

The CS3 ISA is organized into six categories:

- **Compute** — SIMD-8 arithmetic, FMA, activations (ReLU, GELU, Sigmoid, Tanh), transcendentals, quantization casts
- **Mesh Send/Recv** — Directional `SEND_*` / `RECV_*` / `WAIT_*` for the 16-bit bidirectional fabric
- **Memory** — Direct SRAM load/store, auto-increment, DSD (Data Structure Descriptor) tensor addressing
- **Control** — SIMD lane masking, conditional/unconditional branches, barrier sync, halt
- **System** — Clock control (750–1400 MHz), cycle counter, core ID, telemetry

See [`docs/isa/README.md`](docs/isa/README.md) for the full indexed instruction reference.

## Programming Model

Computation follows the **Tungsten dataflow model**: each core executes a program that stalls on `WAIT_*` until data arrives from a mesh neighbor, processes it via SIMD compute, then forwards results to downstream cores via `SEND_*`. Bulk stencil patterns (finite difference, convolution) map directly onto the 2D core grid.

See [`docs/tungsten.md`](docs/tungsten.md) for an overview of the Tungsten domain translation system.
