#include "buffer.h"

// Parse a buffer at a given offset to read a buf_t, the offset is incremented accordingly
// param[in]        <in_bufer>  the total buffer to parse
// param[in]        <in_size>   the total size of the buffer to parse
// param[out]       <out>       the buf_t read from in_bufer at offset, can by 0 sized
// param[in/out]    <offset>    the current offset at wich we are in <in_bufer>
int parse_to_sized_buffer(uint8_t *in_bufer, size_t in_size, buf_t *out, size_t *offset) {
    if (*offset + 1 > in_size) {
        // We can't even read the size
        return -1;
    }

    // Read the size
    out->size = in_bufer[*offset];
    ++*offset;
    if (*offset + out->size > in_size) {
        // Not enough bytes to read buffer size
        return -1;
    }

    // Read the data if there is any
    if (out->size != 0) {
        out->bytes = &(in_bufer[*offset]);
    }
    *offset += out->size;

    return 0;
}
