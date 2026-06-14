# Cerebras CS3 Simulator Project Overview

## Project Goal
This project is a high-fidelity simulator for the Cerebras CS3 Wafer-Scale Engine. The goal is to model the hardware architecture, interconnects, and execution environment to enable performance analysis and software development for CS3-like architectures.

## Hardware Specifications (Target)
- **Core Array:** 800 x 900 2D Mesh (720,000 total cores)
- **On-Chip Memory:** 48KB SRAM per core
- **Clock Speeds:**
  - Base: 750 - 850 MHz
  - Boost: 1.2 GHz
  - Max Boost: 1.4 GHz
- **Compute Capability:** 8-wide SIMD per core
- **Interconnect:** 16-bit per cycle bidirectional mesh (North, South, East, West)
- **IO:** 12x 100 Gbps interfaces
- **External Systems:** Weight server integration for model parameter distribution

## Architecture Philosophy
The simulator focuses on the dataflow nature of the Wafer-Scale Engine, where computation is triggered by the arrival of data at the Processing Elements (PEs).

## Project Structure
- `/docs`: Technical specifications and project documentation
- `/src`: Simulator implementation
- `/tests`: Validation suites
- `/scripts`: Tooling for configuration and execution
