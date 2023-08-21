/*****************************************************************************
 *   Ledger App Boilerplate.
 *   (c) 2021 Ledger SAS.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *****************************************************************************/

#include <stdint.h>
#include <string.h>

#include "os.h"
#include "ux.h"
#include "globals.h"
#include "swap_errors.h"

#ifdef HAVE_NBGL
#include "nbgl_touch.h"
#include "nbgl_page.h"
#endif  // HAVE_NBGL

#ifdef HAVE_BAGL
void io_seproxyhal_display(const bagl_element_t *element) {
    io_seproxyhal_display_default(element);
}
#endif  // HAVE_BAGL

uint8_t io_event(uint8_t channel) {
    (void) channel;

    switch (G_io_seproxyhal_spi_buffer[0]) {
        case SEPROXYHAL_TAG_BUTTON_PUSH_EVENT:
#ifdef HAVE_BAGL
            UX_BUTTON_PUSH_EVENT(G_io_seproxyhal_spi_buffer);
#endif  // HAVE_BAGL
            break;
        case SEPROXYHAL_TAG_STATUS_EVENT:
            if (G_io_apdu_media == IO_APDU_MEDIA_USB_HID &&  //
                !(U4BE(G_io_seproxyhal_spi_buffer, 3) &      //
                  SEPROXYHAL_TAG_STATUS_EVENT_FLAG_USB_POWERED)) {
                THROW(EXCEPTION_IO_RESET);
            }
            /* fallthrough */
            __attribute__((fallthrough));
        case SEPROXYHAL_TAG_DISPLAY_PROCESSED_EVENT:
#ifdef HAVE_BAGL
            UX_DISPLAYED_EVENT({});
#endif  // HAVE_BAGL
#ifdef HAVE_NBGL
            UX_DEFAULT_EVENT();
#endif  // HAVE_NBGL
            break;
#ifdef HAVE_NBGL
        case SEPROXYHAL_TAG_FINGER_EVENT:
            UX_FINGER_EVENT(G_io_seproxyhal_spi_buffer);
            break;
#endif  // HAVE_NBGL
        case SEPROXYHAL_TAG_TICKER_EVENT:
            UX_TICKER_EVENT(G_io_seproxyhal_spi_buffer, {});
            break;
        default:
            UX_DEFAULT_EVENT();
            break;
    }

    if (!io_seproxyhal_spi_is_status_sent()) {
        io_seproxyhal_general_status();
    }

    return 1;
}

uint16_t io_exchange_al(uint8_t channel, uint16_t tx_len) {
    switch (channel & ~(IO_FLAGS)) {
        case CHANNEL_KEYBOARD:
            break;
        case CHANNEL_SPI:
            if (tx_len) {
                io_seproxyhal_spi_send(G_io_apdu_buffer, tx_len);

                if (channel & IO_RESET_AFTER_REPLIED) {
                    halt();
                }

                return 0;
            } else {
                return io_seproxyhal_spi_recv(G_io_apdu_buffer, sizeof(G_io_apdu_buffer), 0);
            }
        default:
            THROW(INVALID_PARAMETER);
    }

    return 0;
}

// recv()
// send()
// recv()
// UI
// recv(ASYNC)
//   send()->io_exchange(RETURN)
// recv()
//
//             READY         RECEIVED          WAITING_USER
// recv()   to Received  ASYNC+to waiting          ERROR
// send()      ERROR         to ready      RETURN_AFTER_RX + to ready

typedef enum io_state { READY, RECEIVED, WAITING_USER } io_state_e;

int output_length = 0;
io_state_e io_state = READY;

void init_io(void) {
    output_length = 0;
    io_state = READY;
}

int recv_apdu(void) {
    PRINTF("Im inside recv_apdu\n");
    switch (io_state) {
        case READY:
            PRINTF("In state READY\n");
            io_state = RECEIVED;
            return io_exchange(CHANNEL_APDU, output_length);
        case RECEIVED:
            PRINTF("In state RECEIVED\n");
            io_state = WAITING_USER;
            int ret = io_exchange(CHANNEL_APDU | IO_ASYNCH_REPLY, output_length);
            io_state = RECEIVED;
            return ret;
        case WAITING_USER:
            PRINTF("Error: Unexpected recv call in WAITING_USER state\n");
            io_state = READY;
            return -1;
    };
    PRINTF("ERROR unknown state\n");
    return -1;
}

// return -1 in case of error
int send_apdu(uint8_t *buffer, size_t buffer_length) {
    memmove(G_io_apdu_buffer, buffer, buffer_length);
    output_length = buffer_length;
    PRINTF("Sending apdu\n");
    switch (io_state) {
        case READY:
            PRINTF("Error: Unexpected send call in READY state\n");
            return -1;
        case RECEIVED:
            io_state = READY;
            return 0;
        case WAITING_USER:
            PRINTF("Sending reply with IO_RETURN_AFTER_TX\n");
            io_exchange(CHANNEL_APDU | IO_RETURN_AFTER_TX, output_length);
            output_length = 0;
            io_state = READY;
            return 0;
    }
    PRINTF("Error: Unknown io_state\n");
    return -1;
}

int reply_error(swap_error_e error) {
    uint8_t output_buffer[2] = {(error >> 8) & 0xFF, error & 0xFF};
    return send_apdu(output_buffer, 2);
}

int reply_success(void) {
    return reply_error(SUCCESS);
}

int instant_reply_success(void) {
    G_io_apdu_buffer[0] = 0x90;
    G_io_apdu_buffer[1] = 0x00;
    return io_exchange(CHANNEL_APDU | IO_RETURN_AFTER_TX, 2);
}
