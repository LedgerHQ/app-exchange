#include "parse_check_address_message.h"
#include "globals.h"

// Small wrapper around parse_to_sized_buffer as the DER signature encompasses the
// first special byte and the size byte
static int parse_der_signature(uint8_t *in, size_t in_size, buf_t *der, size_t *offset) {
    // Ignore first bytes 0x30
    ++*offset;

    // Read compoind object
    if (parse_to_sized_buffer(in, in_size, der, offset) != 0) {
        return -1;
    }
    // Adapt buffer to encompass the full DER signature
    der->size += 2;
    der->bytes = &der->bytes[-2];
    return 0;
}

//                                                      offset
// 1 byte (length X of "to" currency configuration)     0
// X bytes ("to" currency configuration)                1
// D bytes = 2 + C (DER serialized signature):          1 + X
//    1 byte 0x30                                       1 + X
//    1 byte length C of compoind object                2 + X
//    C bytes
// 1 byte length Y of address paramaters                1 + X + D
// Y bytes of address parameters                        2 + X + D
int parse_check_address_message(const command_t *cmd,
                                buf_t *config,
                                buf_t *der,
                                buf_t *address_parameters) {
    size_t total_read = 0;

    // Read currency configuration
    if (parse_to_sized_buffer(cmd->data.bytes, cmd->data.size, config, &total_read) != 0) {
        PRINTF("Cannot read the config\n");
        return 0;
    }
    if (config->size < 1) {
        PRINTF("Invalid config size %d\n", config->size);
        return 0;
    }

    if (parse_der_signature(cmd->data.bytes, cmd->data.size, der, &total_read) != 0) {
        PRINTF("Cannot parse the DER signature\n");
        return 0;
    }
    if (der->size < MIN_DER_SIGNATURE_LENGTH || der->size > MAX_DER_SIGNATURE_LENGTH) {
        PRINTF("Invalid DER signature size %d\n", der->size);
        return 0;
    }

    // Read address parameters
    if (parse_to_sized_buffer(cmd->data.bytes, cmd->data.size, address_parameters, &total_read) !=
        0) {
        PRINTF("Cannot read the address_parameters\n");
        return 0;
    }
    if (address_parameters->size < 1) {
        PRINTF("Invalid address_parameters size %d\n", address_parameters->size);
        return 0;
    }

    // Check that there is nothing else to read
    if (cmd->data.size != total_read) {
        PRINTF("Bytes to read: %d, bytes read: %d\n", cmd->data.size, total_read);
        return 0;
    }

    return 1;
}
