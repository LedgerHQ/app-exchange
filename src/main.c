/*******************************************************************************
*   Ledger Blue
*   (c) 2016 Ledger
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
********************************************************************************/

#include "init.h"
#include "menu.h"
#include "swap_app_context.h"
#include "commands.h"
#include "power_ble.h"
#include "command_dispatcher.h"
#include "apdu_offsets.h"

unsigned char G_io_seproxyhal_spi_buffer[IO_SEPROXYHAL_BUFFER_SIZE_B];

#define CLA 0xE0

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

typedef enum io_state {
    READY,
    RECEIVED,
    WAITING_USER
} io_state_e;

int output_length = 0;
io_state_e io_state = READY;

int recv_apdu() {
    switch (io_state) {
        case READY:
            io_state = RECEIVED;
            return io_exchange(CHANNEL_APDU, output_length);
        case RECEIVED:
            io_state = WAITING_USER;
            return io_exchange(CHANNEL_APDU | IO_ASYNCH_REPLY, output_length);
        case WAITING_USER:
            PRINTF("Error: Unexpected recv call in WAITING_USER state");
            io_state = READY;
            return -1;
    };
    return -1;
}

// return -1 in case of error
int send_apdu(unsigned char* buffer, unsigned int buffer_length) {
    os_memmove(G_io_apdu_buffer, buffer, buffer_length);
    output_length = buffer_length;
    switch (io_state) {
        case READY:
            PRINTF("Error: Unexpected send call in READY state");
            return -1;
        case RECEIVED:
            io_state = READY;
            return 0;
        case WAITING_USER:
            io_exchange(CHANNEL_APDU | IO_RETURN_AFTER_TX, output_length);
            output_length = 0;
            io_state = READY;
            return 0;
    }
    return -1;
}

void app_main(void) {
    int input_length = 0;
    swap_app_context_t ctx;
    init_application_context(&ctx);
    ui_idle();    
    for(;;) {
        input_length = recv_apdu();
        if (input_length == -1) // there were an error, lets start from the beginning
            return;
        if (input_length <= OFFSET_INS ||
            G_io_apdu_buffer[OFFSET_CLA] != CLA ||
            G_io_apdu_buffer[OFFSET_INS] >= COMMAND_UPPER_BOUND) {
            PRINTF("Error: bad APDU");
            return;
        }
        if (dispatch_command(G_io_apdu_buffer[OFFSET_INS], &ctx, G_io_apdu_buffer + OFFSET_CDATA, input_length - OFFSET_CDATA, send_apdu) < 0)
            return; // some non recoverable error happened
        if (ctx.state == INITIAL_STATE) {
            ui_idle();
        }
    }
}

// override point, but nothing more to do
void io_seproxyhal_display(const bagl_element_t *element) {
    io_seproxyhal_display_default((bagl_element_t*)element);
}

unsigned char io_event(unsigned char channel) {
    // nothing done with the event, throw an error on the transport layer if
    // needed
    // can't have more than one tag in the reply, not supported yet.
    switch (G_io_seproxyhal_spi_buffer[0]) {
        case SEPROXYHAL_TAG_FINGER_EVENT:
            UX_FINGER_EVENT(G_io_seproxyhal_spi_buffer);
            break;

        case SEPROXYHAL_TAG_BUTTON_PUSH_EVENT:
            UX_BUTTON_PUSH_EVENT(G_io_seproxyhal_spi_buffer);
            break;

        case SEPROXYHAL_TAG_STATUS_EVENT:
            if (G_io_apdu_media == IO_APDU_MEDIA_USB_HID && !(U4BE(G_io_seproxyhal_spi_buffer, 3) & SEPROXYHAL_TAG_STATUS_EVENT_FLAG_USB_POWERED)) {
                THROW(EXCEPTION_IO_RESET);
            }
            // no break is intentional
        default:
            UX_DEFAULT_EVENT();
            break;

        case SEPROXYHAL_TAG_DISPLAY_PROCESSED_EVENT:
            UX_DISPLAYED_EVENT({});
            break;

        case SEPROXYHAL_TAG_TICKER_EVENT:
            UX_TICKER_EVENT(G_io_seproxyhal_spi_buffer, {});
            break;
    }

    // close the event if not done previously (by a display or whatever)
    if (!io_seproxyhal_spi_is_status_sent()) {
        io_seproxyhal_general_status();
    }

    // command has been processed, DO NOT reset the current APDU transport
    return 1;
}


unsigned short io_exchange_al(unsigned char channel, unsigned short tx_len) {
    switch (channel & ~(IO_FLAGS)) {
        case CHANNEL_KEYBOARD:
            break;

        // multiplexed io exchange over a SPI channel and TLV encapsulated protocol
        case CHANNEL_SPI:
            if (tx_len) {
                io_seproxyhal_spi_send(G_io_apdu_buffer, tx_len);

                if (channel & IO_RESET_AFTER_REPLIED) {
                    reset();
                }
                return 0; // nothing received from the master so far (it's a tx
                        // transaction)
            } else {
                return io_seproxyhal_spi_recv(G_io_apdu_buffer,
                                            sizeof(G_io_apdu_buffer), 0);
            }

        default:
            THROW(INVALID_PARAMETER);
    }
    return 0;
}


void app_exit(void) {

    BEGIN_TRY_L(exit) {
        TRY_L(exit) {
            os_sched_exit(-1);
        }
        FINALLY_L(exit) {

        }
    }
    END_TRY_L(exit);
}

__attribute__((section(".boot"))) int main(int arg0) {
    // exit critical section
    __asm volatile("cpsie i");

    // ensure exception will work as planned
    os_boot();

    for (;;) {
        UX_INIT();

        BEGIN_TRY {
            TRY {
                io_seproxyhal_init();

                USB_power(0);
                USB_power(1);
                power_ble();
              
                app_main();
            }
            CATCH(EXCEPTION_IO_RESET) {
                // reset IO and UX before continuing
                CLOSE_TRY;
                continue;
            }
            CATCH_ALL {
                CLOSE_TRY;
                break;
            }
            FINALLY {
            }
        }
        END_TRY;
    }
    app_exit();
    return 0;
}
