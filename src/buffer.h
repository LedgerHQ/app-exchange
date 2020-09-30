#pragma once

#include <stddef.h>
#include <stdint.h>

typedef struct buf_s {
    uint8_t *bytes;
    size_t size;
} buf_t;
