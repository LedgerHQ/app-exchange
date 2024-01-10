#include "buffer.h"
#include "os.h"

// Parse a buffer at a given offset to read a buf_t, the offset is incremented accordingly
// param[in]        <in_buffer>            the total buffer to parse
// param[in]        <in_size>              the total size of the buffer to parse
// param[in]        <size_of_length_field> the size of the length field in the header
// param[out]       <out>                  the buf_t read from in_buffer at offset, can by 0 sized
// param[in/out]    <offset>               the current offset at which we are in <in_buffer>
bool parse_to_sized_buffer(uint8_t *in_buffer,
                           uint16_t in_size,
                           uint8_t size_of_length_field,
                           buf_t *out,
                           uint16_t *offset) {
    if (*offset + size_of_length_field > in_size) {
        // We can't even read the size
        PRINTF("Failed to read the header sized %d, only %d bytes available\n",
               size_of_length_field,
               in_size);
        return false;
    }

    // Read the size
    if (size_of_length_field == 1) {
        out->size = in_buffer[*offset];
    } else if (size_of_length_field == 2) {
        out->size = U2BE(in_buffer, *offset);
    } else {
        PRINTF("Unable to read a %d sized header\n", size_of_length_field);
        return false;
    }
    *offset += size_of_length_field;

    // Cast before comparison to avoid potential int overflow
    if (((uint32_t) *offset) + out->size > in_size) {
        PRINTF("Not enough remaining bytes to read. Total %d, offset %d, claims %d bytes\n",
               in_size,
               *offset,
               out->size);
        return false;
    }

    // Read the data if there is any
    if (out->size != 0) {
        out->bytes = &(in_buffer[*offset]);
    } else {
        out->bytes = NULL;
    }
    *offset += out->size;

    return true;
}

// Parse a buffer at a given offset to read a buf_t, the offset is incremented accordingly
// param[in]        <in_buffer>  the total buffer to parse
// param[in]        <in_size>   the total size of the buffer to parse
// param[out]       <out>       the int read from in_buffer at offset
// param[in/out]    <offset>    the current offset at which we are in <in_buffer>
bool pop_uint8_from_buffer(uint8_t *in_buffer, uint16_t in_size, uint8_t *out, uint16_t *offset) {
    if (*offset + 1 > in_size) {
        PRINTF("Failed to read the uint, only %d bytes available\n", in_size);
        return false;
    }
    *out = in_buffer[*offset];
    *offset += 1;

    return true;
}
