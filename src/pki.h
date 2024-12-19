#pragma once

#include <cx.h>
#include <os.h>
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#include "buf.h"
#include "swap_errors.h"

swap_error_e check_signature_with_pki(const uint8_t *buffer,
                                      uint8_t buffer_length,
                                      uint8_t expected_key_usage,
                                      cx_curve_t expected_curve,
                                      const cbuf_t *signature);
