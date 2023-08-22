#pragma once

#include <stdint.h>

#include "ux.h"
#include "os_io_seproxyhal.h"
#include "swap_errors.h"

#ifdef HAVE_BAGL
void io_seproxyhal_display(const bagl_element_t *element);
#endif  // HAVE_BAGL

/**
 * IO callback called when an interrupt based channel has received
 * data to be processed.
 *
 * @return 1 if success, 0 otherwise.
 *
 */
uint8_t io_event(uint8_t channel);

uint16_t io_exchange_al(uint8_t channel, uint16_t tx_len);

void init_io(void);

int recv_apdu(void);

int send_apdu(uint8_t *buffer, size_t buffer_length);

int reply_error(swap_error_e error);

int reply_success(void);

int instant_reply_success(void);
