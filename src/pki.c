#include "os.h"
#include "cx.h"
#include "pki.h"
#include "os_pki.h"

swap_error_e check_signature_with_pki(const uint8_t *buffer,
                                      uint8_t buffer_length,
                                      uint8_t expected_key_usage,
                                      cx_curve_t expected_curve,
                                      const cbuf_t *signature) {
    uint8_t key_usage = 0;
    size_t certificate_name_len = 0;
    uint8_t certificate_name[CERTIFICATE_TRUSTED_NAME_MAXLEN] = {0};
    cx_ecfp_384_public_key_t public_key = {0};

    bolos_err_t bolos_err;
    bolos_err = os_pki_get_info(&key_usage, certificate_name, &certificate_name_len, &public_key);
    if (bolos_err != 0x0000) {
        PRINTF("Error %x while getting PKI certificate info\n", bolos_err);
        return NO_CERTIFICATE_LOADED;
    }

    if (key_usage != expected_key_usage) {
        PRINTF("Wrong usage certificate %d, expected %d\n", key_usage, expected_key_usage);
        return WRONG_CERTIFICATE_DATA;
    }

    if (public_key.curve != expected_curve) {
        PRINTF("Wrong curve %d, expected %d\n", public_key.curve, expected_curve);
        return WRONG_CERTIFICATE_DATA;
    }

    PRINTF("Certificate '%s' loaded with success\n", certificate_name);

    // Checking the signature with PKI
    if (!os_pki_verify((uint8_t *) buffer,
                       buffer_length,
                       (uint8_t *) signature->bytes,
                       signature->size)) {
        PRINTF("Error, '%.*H' is not a signature of buffer '%.*H' by the PKI key '%.*H'\n",
               signature->size,
               signature->bytes,
               buffer_length,
               buffer,
               sizeof(public_key),
               &public_key);
        return WRONG_TLV_SIGNATURE;
    }

    PRINTF("Signature verified successfully\n");
    return SUCCESS;
}
