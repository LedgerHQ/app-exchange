/*****************************************************************************
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
 *****************************************************************************/

#include "os.h"
#include "os_io_seproxyhal.h"
#include "init.h"
#include "menu.h"
#include "swap_app_context.h"
#include "commands.h"
#include "command_dispatcher.h"
#include "apdu_offsets.h"
#include "swap_errors.h"
#include "reply_error.h"

#include "usbd_core.h"
#define CLA 0xE0

unsigned char G_io_seproxyhal_spi_buffer[IO_SEPROXYHAL_BUFFER_SIZE_B];
swap_app_context_t swap_ctx;

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

int recv_apdu() {
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
int send_apdu(unsigned char *buffer, unsigned int buffer_length) {
    os_memmove(G_io_apdu_buffer, buffer, buffer_length);
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

void app_main(void) {
    int input_length = 0;

    output_length = 0;
    io_state = READY;
    for (;;) {
        input_length = recv_apdu();
        PRINTF("New APDU received:\n%.*H\n", input_length, G_io_apdu_buffer);
        if (input_length == -1)  // there were an error, lets start from the beginning
            return;
        if (input_length <= OFFSET_INS ||                           //
            G_io_apdu_buffer[OFFSET_CLA] != CLA ||                  //
            G_io_apdu_buffer[OFFSET_INS] <= COMMAND_LOWER_BOUND ||  //
            G_io_apdu_buffer[OFFSET_INS] >= COMMAND_UPPER_BOUND) {
            PRINTF("Error: bad APDU\n");
            reply_error(&swap_ctx, INVALID_INSTRUCTION, send_apdu);
            continue;
        }

        if (dispatch_command(G_io_apdu_buffer[OFFSET_INS],     //
                             G_io_apdu_buffer[OFFSET_P2],      //
                             &swap_ctx,                        //
                             G_io_apdu_buffer + OFFSET_CDATA,  //
                             input_length - OFFSET_CDATA,      //
                             send_apdu) < 0)
            return;  // some non recoverable error happened

        if (swap_ctx.state == INITIAL_STATE) {
            ui_idle();
        }
    }
}

void app_exit(void) {
    BEGIN_TRY_L(exit) {
        TRY_L(exit) { os_sched_exit(-1); }
        FINALLY_L(exit) {}
    }
    END_TRY_L(exit);
}

__attribute__((section(".boot"))) int main(int arg0) {
    // exit critical section
    __asm volatile("cpsie i");

    // ensure exception will work as planned
    os_boot();

    for (;;) {
        ux_init();

        BEGIN_TRY {
            TRY {
                io_seproxyhal_init();

#ifdef TARGET_NANOX
                // grab the current plane mode setting
                G_io_app.plane_mode = os_setting_get(OS_SETTING_PLANEMODE, NULL, 0);
#endif  // TARGET_NANOX

                init_application_context(&swap_ctx);

                USB_power(0);
                USB_power(1);

                ui_idle();

#ifdef HAVE_BLE
                BLE_power(0, NULL);
                BLE_power(1, "Nano X");
#endif

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
            FINALLY {}
        }
        END_TRY;
    }
    app_exit();
    return 0;
}
