#pragma once

#include <stdint.h>
#include <stdbool.h>

// Mesh Packet definition
typedef struct {
    uint16_t payload;
    uint8_t source_dir;
    uint8_t flags;
} MeshPacket;

// Fixed-size FIFO queue for MeshPackets
typedef struct {
    MeshPacket packets[16];
    int head;
    int tail;
    int size;
} MeshBuffer;

// Mesh Node state for a single core
typedef struct {
    MeshBuffer buffers[4]; // North, South, East, West
    uint16_t core_x;
    uint16_t core_y;
} CS3MeshNode;

// The global Mesh Network
// Represented as a 2D array of mesh nodes
extern CS3MeshNode mesh[800][900];

// Function prototypes for mesh operations
void send_packet(uint16_t x, uint16_t y, uint8_t dir, MeshPacket pkt);
bool has_packet(uint16_t x, uint16_t y, uint8_t dir);
MeshPacket pop_packet(uint16_t x, uint16_t y, uint8_t dir);
bool has_any_packet(uint16_t x, uint16_t y);
