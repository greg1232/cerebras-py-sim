#pragma once

#include <stdint.h>
#include <stdbool.h>

// Clock frequency constants
#define CLK_BASE 750
#define CLK_MID 850
#define CLK_BOOST 1200
#define CLK_MAX 1400

// Mesh Directions
typedef enum {
    NORTH = 0,
    SOUTH = 1,
    EAST = 2,
    WEST = 3
} Direction;

// SIMD-8 Vector Register
typedef union {
    float f32[8];
    uint16_t i16[8];
    int8_t i8[8];
} VectorReg;

// Data Structure Descriptor (DSD) State
typedef struct {
    uint32_t base_addr;
    uint32_t stride;
    uint32_t limit;
    uint32_t current_ptr;
} DSDState;

// Core State
typedef struct {
    VectorReg regs[32];
    uint32_t pc;
    uint32_t mask;
    uint8_t sram[48 * 1024];
    DSDState dsd;
    uint64_t clock_freq;
    uint64_t tick_counter;
    uint16_t core_x;
    uint16_t core_y;
    bool halted;
    uint32_t smi_status;
} CS3CoreState;
