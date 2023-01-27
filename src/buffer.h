#pragma once

#include <stddef.h>
#include <stdint.h>

typedef struct buf_s {
    uint8_t *bytes;
    size_t size;
} buf_t;

int parse_to_sized_buffer(uint8_t *in, size_t in_size, buf_t *out, size_t *offset);
