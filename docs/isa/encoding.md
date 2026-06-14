# CS3 Simulator ISA: Binary Instruction Encoding

This document specifies the 32-bit fixed-width instruction encoding for the CS3 simulator ISA.

## Instruction Formats

The ISA uses six primary instruction formats. All instructions are 32 bits wide.

### R-Type (Register-Register)
Used for compute SIMD and cast operations.
```
| 31      26 | 25    21 | 20    16 | 15    11 | 10      0 |
|   Opcode   |    rd    |    rs1   |    rs2   |    func    |
```
- `Opcode` (6 bits): Major opcode for the instruction group.
- `rd` (5 bits): Destination register (0-31).
- `rs1` (5 bits): Source register 1 (0-31).
- `rs2` (5 bits): Source register 2 (0-31).
- `func` (11 bits): Function subcode to distinguish operations within the group.

### M-Type (Mesh)
Used for mesh network communication.

**Runtime Constraint:** The effective destination of mesh instructions is constrained by the current Block configuration; boundary crossings are blocked by hardware.

```
| 31      26 | 25    21 | 20    18 | 17      0 |
|   Opcode   |    reg    | direction |   unused   |
```
- `Opcode` (6 bits): Major opcode for mesh operations.
- `reg` (5 bits): Register to send from or receive into (0-31).
- `direction` (3 bits): Mesh direction (North=0, South=1, East=2, West=3).
- `unused` (18 bits): Reserved.

### I-Type (Immediate/Memory)
Used for memory access and system operations.
```
| 31      26 | 25    21 | 20      0 |
|   Opcode   |   rd/rs   |    imm16   |
```
- `Opcode` (6 bits): Major opcode for memory/system operations.
- `rd/rs` (5 bits): Destination or source register (0-31).
- `imm16` (16 bits): Signed 16-bit immediate value or offset.

### D-Type (DSD)
Used for Data Structure Descriptor operations.
```
| 31      26 | 25    21 | 20      0 |
|   Opcode   |   rd/rs   |  dsd_field |
```
- `Opcode` (6 bits): Major opcode for DSD operations.
- `rd/rs` (5 bits): Register used for base/stride/limit (0-31).
- `dsd_field` (16 bits): Field selector or immediate configuration.

### C-Type (Control)
Used for branching and mask control.
```
| 31      26 | 25    21 | 20      0 |
|   Opcode   |    rs    | target/imm |
```
- `Opcode` (6 bits): Major opcode for control operations.
- `rs` (5 bits): Source register for condition checking (0-31).
- `target/imm` (16 bits): Branch target offset or mask immediate.

### S-Type (System)
Used for clock and identity configuration.
```
| 31      26 | 25    21 | 20      0 |
|   Opcode   |    rd    |    imm     |
```
- `Opcode` (6 bits): Major opcode for system operations.
- `rd` (5 bits): Destination register for reading system values (0-31).
- `imm` (16 bits): Immediate value for setting system configuration.

---

## Major Opcode Table

| Instruction Group | Opcode (Hex) | Format | Description |
| :--- | :--- | :--- | :--- |
| COMPUTE_SIMD | 0x01 | R | Vector arithmetic and activations |
| CAST | 0x02 | R | Type casting and clipping |
| MESH | 0x03 | M | Mesh send, receive, and sync |
| MEMORY | 0x04 | I | SRAM Load/Store |
| DSD | 0x05 | D | Data Structure Descriptor mgmt |
| CONTROL | 0x06 | C | Branching and masking |
| SYSTEM | 0x07 | S | Core system configuration |

---

## Function Subcode Tables

### Compute SIMD (`Opcode 0x01`)
| Instruction | func (Hex) | Description |
| :--- | :--- | :--- |
| VADD | 0x000 | Vector Addition |
| VSUB | 0x001 | Vector Subtraction |
| VMUL | 0x002 | Vector Multiplication |
| VDIV | 0x003 | Vector Division |
| VFMADD | 0x004 | Vector Fused Multiply-Add |
| VABS | 0x005 | Vector Absolute Value |
| VMAX | 0x006 | Vector Maximum |
| VMIN | 0x007 | Vector Minimum |
| VNEG | 0x008 | Vector Negation |
| VRELU | 0x009 | Vector ReLU |
| VGELU | 0x00A | Vector GELU |
| VSIGMOID | 0x00B | Vector Sigmoid |
| VTANH | 0x00C | Vector Tanh |
| VEXP | 0x00D | Vector Exponential |
| VLOG | 0x00E | Vector Logarithm |
| VSQRT | 0x00F | Vector Square Root |

### Cast (`Opcode 0x02`)
| Instruction | func (Hex) | Description |
| :--- | :--- | :--- |
| VCAST_F16_F32 | 0x000 | Cast FP16 to FP32 |
| VCAST_F32_F16 | 0x001 | Cast FP32 to FP16 |
| VCAST_I8_F16 | 0x002 | Cast I8 to FP16 |
| VCAST_F16_I8 | 0x003 | Cast FP16 to I8 |
| VCLIP | 0x004 | Vector Clipping |

### Mesh Operations (`Opcode 0x03`)
These are differentiated by the `direction` field in the M-Type format.
- North: 0, South: 1, East: 2, West: 3.
- Instructions use the `opcode` for the primary action (SEND, RECV, WAIT), but for this ISA, the Opcode 0x03 serves as the group. Specific instructions are mapped as follows:
    - SEND: Opcode 0x03 + direction
    - RECV: Opcode 0x03 + direction (handled via internal micro-op or extended opcode)
    - WAIT: Opcode 0x03 + direction
    - POLL_MESH: Opcode 0x03 + direction 0 (Special case)

### Memory (`Opcode 0x04`)
| Instruction | Encoding Detail | Description |
| :--- | :--- | :--- |
| LDR | Opcode 0x04 | Load Register |
| STR | Opcode 0x04 | Store Register |
| LDR_INC | Opcode 0x04 | Load Register and Increment |
| STR_INC | Opcode 0x04 | Store Register and Increment |

### DSD (`Opcode 0x05`)
| Instruction | Encoding Detail | Description |
| :--- | :--- | :--- |
| SET_DSD | Opcode 0x05 | Set DSD Configuration |
| LDR_DSD | Opcode 0x05 | Load via DSD |
| STR_DSD | Opcode 0x05 | Store via DSD |
| NEXT_DSD | Opcode 0x05 | Advance DSD Pointer |

### Control (`Opcode 0x06`)
| Instruction | Encoding Detail | Description |
| :--- | :--- | :--- |
| VMASK | Opcode 0x06 | Set Vector Mask |
| B_COND | Opcode 0x06 | Conditional Branch |
| B_JMP | Opcode 0x06 | Unconditional Jump |
| SYNC | Opcode 0x06 | Mesh Synchronization Barrier |
| HALT | Opcode 0x06 | Halt Core Execution |

### System (`Opcode 0x07`)
| Instruction | Encoding Detail | Description |
| :--- | :--- | :--- |
| SET_CLK | Opcode 0x07 | Set Clock Frequency |
| GET_TICK | Opcode 0x07 | Get Clock Tick Count |
| SET_ID | Opcode 0x07 | Set Core Identity |
| SMI_READ | Opcode 0x07 | Read System Management Interface |
