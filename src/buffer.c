#include "buffer.h"

// Parse a buffer at a given offset to read a buf_t, the offset is incremented accordingly
// param[in]        <in_buffer>  the total buffer to parse
// param[in]        <in_size>   the total size of the buffer to parse
// param[out]       <out>       the buf_t read from in_buffer at offset, can by 0 sized
// param[in/out]    <offset>    the current offset at wich we are in <in_buffer>
bool parse_to_sized_buffer(uint8_t *in_buffer, uint16_t in_size, buf_t *out, uint16_t *offset) {
    if (*offset + 1 > in_size) {
        // We can't even read the size
        return false;
    }

    // Read the size
    out->size = in_buffer[*offset];
    ++*offset;
    if (*offset + out->size > in_size) {
        // Not enough bytes to read buffer size
        return false;
    }

    // Read the data if there is any
    if (out->size != 0) {
        out->bytes = &(in_buffer[*offset]);
    }
    *offset += out->size;

    return true;
}
