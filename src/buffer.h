#pragma once

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct buf_s {
    uint8_t *bytes;
    uint16_t size;
} buf_t;

bool parse_to_sized_buffer(uint8_t *in_buffer, uint16_t in_size, buf_t *out, uint16_t *offset);
