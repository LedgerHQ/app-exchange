#pragma once

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

typedef struct buf_s {
    uint8_t *bytes;
    uint16_t size;
} buf_t;

typedef struct cbuf_s {
    const uint8_t *bytes;
    uint16_t size;
} cbuf_t;

bool parse_to_sized_buffer(uint8_t *in_buffer,
                           uint16_t in_size,
                           uint8_t size_of_length_field,
                           buf_t *out,
                           uint16_t *offset);

bool pop_uint8_from_buffer(uint8_t *in_buffer, uint16_t in_size, uint8_t *out, uint16_t *offset);
