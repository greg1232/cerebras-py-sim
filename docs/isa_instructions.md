# CS3 ISA: Instruction Reference

## 1. Compute Instructions (SIMD-8)
All compute instructions operate on the 8-wide vector registers.

### Arithmetic
- `VADD`: Vector Addition
- `VSUB`: Vector Subtraction
- `VMUL`: Vector Multiplication
- `VDIV`: Vector Division
- `VFMADD`: Vector Fused Multiply-Add (C = A * B + C)
- `VABS`: Vector Absolute Value
- `VMAX`: Vector Maximum
- `VMIN`: Vector Minimum
- `VNEG`: Vector Negation

### Activations & Special Functions
- `VRELU`: Rectified Linear Unit
- `VGE LU`: Gaussian Error Linear Unit
- `VSIGMOID`: Sigmoid Approximation
- `VTANH`: Hyperbolic Tangent Approximation
- `VEXP`: Vector Exponential
- `VLOG`: Vector Logarithm
- `VSQRT`: Vector Square Root

### Casting & Quantization
- `VCAST_F16_F32`: Cast FP16 to FP32
- `VCAST_F32_F16`: Cast FP32 to FP16
- `VCAST_I8_F16`: Cast INT8 to FP16
- `VCAST_F16_I8`: Cast FP16 to INT8 (with saturation)
- `VCLIP`: Vector Clip/Clamp to range

## 2. Mesh & Interconnect Instructions
These instructions handle the 16-bit bidirectional mesh communication.

### Data Movement
- `SEND_N`: Send register to North neighbor
- `SEND_S`: Send register to South neighbor
- `SEND_E`: Send register to East neighbor
- `SEND_W`: Send register to West neighbor
- `RECV_N`: Receive from North neighbor
- `RECV_S`: Receive from South neighbor
- `RECV_E`: Receive from East neighbor
- `RECV_W`: Receive from West neighbor

### Dataflow Triggering
- `WAIT_N`: Stall execution until data arrives from North
- `WAIT_S`: Stall execution until data arrives from South
- `WAIT_E`: Stall execution until data arrives from East
- `WAIT_W`: Stall execution until data arrives from West
- `POLL_MESH`: Non-blocking check for any pending mesh data

## 3. Memory Instructions (48KB SRAM)
Direct access to the core's local scratchpad memory.

### Basic Access
- `LDR`: Load from SRAM to register
- `STR`: Store from register to SRAM
- `LDR_INC`: Load and increment pointer
- `STR_INC`: Store and increment pointer

### DSD (Data Structure Descriptor) Operations
- `SET_DSD`: Configure DSD base address, stride, and limit
- `LDR_DSD`: Load using DSD indirect addressing
- `STR_DSD`: Store using DSD indirect addressing
- `NEXT_DSD`: Advance DSD pointer to next element

## 4. Control & System Instructions

### Flow Control
- `VMASK`: Set SIMD lane mask
- `B_COND`: Conditional branch based on mask/flag
- `B_JMP`: Unconditional jump
- `SYNC`: Local core synchronization barrier
- `HALT`: Put core into low-power wait state

### System
- `SET_CLK`: Update local core clock frequency (Base/Boost/Max)
- `GET_TICK`: Read local cycle counter
- `SET_ID`: Set core coordinates (X, Y)
- `SMI_READ`: Read core telemetry/status
