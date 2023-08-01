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
#include "ux.h"
#include "os_io_seproxyhal.h"
#include "init.h"
#include "io.h"
#include "menu.h"
#include "globals.h"
#include "commands.h"
#include "command_dispatcher.h"
#include "apdu_offsets.h"
#include "swap_errors.h"

#include "usbd_core.h"
#define CLA 0xE0

ux_state_t G_ux;
bolos_ux_params_t G_ux_params;

uint8_t G_io_seproxyhal_spi_buffer[IO_SEPROXYHAL_BUFFER_SIZE_B];

typedef struct apdu_s {
    uint8_t ins;
    uint8_t rate;
    uint8_t subcommand;
    uint16_t data_length;
    uint8_t data[510];
} apdu_t;
apdu_t G_received_apdu;

swap_app_context_t G_swap_ctx;


void app_main(void) {
    int input_length = 0;

    init_io();

    for (;;) {
        input_length = recv_apdu();
        PRINTF("New APDU received:\n%.*H\n", input_length, G_io_apdu_buffer);
        // there were a fatal error during APDU reception, restart from the beginning
        // Don't bother trying to send a status code, IOs are probably out
        if (input_length == -1) {
            return;
        }

        if (input_length < OFFSET_CDATA) {
            PRINTF("Error: malformed APDU\n");
            reply_error(MALFORMED_APDU);
            return;
        }
        if (G_io_apdu_buffer[OFFSET_CLA] != CLA) {
            PRINTF("Error: malformed APDU\n");
            reply_error(CLASS_NOT_SUPPORTED);
            return;
        }

        uint8_t ins = G_io_apdu_buffer[OFFSET_INS];
        if (ins != GET_VERSION_COMMAND
            && ins != START_NEW_TRANSACTION_COMMAND
            && ins != SET_PARTNER_KEY_COMMAND
            && ins != CHECK_PARTNER_COMMAND
            && ins != PROCESS_TRANSACTION_RESPONSE_COMMAND
            && ins != CHECK_TRANSACTION_SIGNATURE_COMMAND
            && ins != CHECK_PAYOUT_ADDRESS
            && ins != CHECK_REFUND_ADDRESS
            && ins != START_SIGNING_TRANSACTION) {
            PRINTF("Incorrect instruction %d\n", ins);
            reply_error(INVALID_INSTRUCTION);
            return;
        }

        uint8_t rate = G_io_apdu_buffer[OFFSET_P1];
        if (rate != FIXED && rate != FLOATING) {
            PRINTF("Incorrect P1 %d\n", rate);
            reply_error(WRONG_P1);
            return;
        }

        uint8_t subcommand = G_io_apdu_buffer[OFFSET_P2] & SUBCOMMAND_PART;
        if (subcommand != SWAP
            && subcommand != SELL
            && subcommand != FUND
            && subcommand != SWAP_NG
            && subcommand != SELL_NG
            && subcommand != FUND_NG) {
            PRINTF("Incorrect subcommand %d\n", subcommand);
            reply_error(WRONG_P2_SUBCOMMAND);
            return;
        }

        uint8_t extension = G_io_apdu_buffer[OFFSET_P2] & EXTENSION_PART;
        if ((extension & ~(P2_NONE|P2_MORE|P2_EXTEND)) != 0) {
            PRINTF("Incorrect extension %d\n", extension);
            reply_error(WRONG_P2_EXTENSION);
            return;
        }

        uint8_t data_length = G_io_apdu_buffer[OFFSET_LC];
        if (data_length != input_length - OFFSET_CDATA) {
            PRINTF("Incorrect advertized length %d\n", data_length);
            reply_error(INVALID_DATA_LENGTH);
            return;
        }

        // P2_MORE is set to signal that this APDU buffer is not complete
        // P2_EXTEND is set to signal that this APDU buffer extends a previous one
        bool first_data_chunk = !(extension & P2_EXTEND);
        bool last_data_chunk = !(extension & P2_MORE);

        // if (!first_data_chunk && G_swap_ctx.state != PROVIDER_CHECKED) {
        //     PRINTF("Error: Unexpected !first_data_chunk\n");
        //     reply_error(INVALID_INSTRUCTION);
        //     return;
        // }

        // if (!last_data_chunk && G_swap_ctx.state != PROVIDER_CHECKED) {
        //     PRINTF("Error: Unexpected !first_data_chunk\n");
        //     reply_error(INVALID_INSTRUCTION);
        //     return;
        // }

        if (first_data_chunk) {
            PRINTF("Receiving the first part of an apdu\n");
            G_received_apdu.ins = ins;
            G_received_apdu.rate = rate;
            G_received_apdu.subcommand = subcommand;
            G_received_apdu.data_length = data_length;
            memcpy(G_received_apdu.data, G_io_apdu_buffer + OFFSET_CDATA, G_received_apdu.data_length);
            PRINTF("P1 G_received_apdu.data_length = %d\n", G_received_apdu.data_length);
            for (int i = 0; i < G_received_apdu.data_length; ++i) {
                PRINTF("%02x", G_received_apdu.data[i]);
            }
            PRINTF("\n");
        } else {
            PRINTF("Extending an already received partial of an apdu\n");
            if (G_received_apdu.ins != ins
                || G_received_apdu.rate != rate
                || G_received_apdu.subcommand != subcommand) {
                PRINTF("Refusing to extend a different apdu\n");
                reply_error(INVALID_PZ_EXTENSION);
                return;
            }
            memcpy(G_received_apdu.data + G_received_apdu.data_length, G_io_apdu_buffer + OFFSET_CDATA, input_length - OFFSET_CDATA);
            G_received_apdu.data_length += input_length - OFFSET_CDATA;

            PRINTF("G_received_apdu.data_length = %d\n", G_received_apdu.data_length);
            for (int i = 0; i < G_received_apdu.data_length; ++i) {
                PRINTF("%02x", G_received_apdu.data[i]);
            }
            PRINTF("\n");
        }

        if (!last_data_chunk) {
            // Reply a blank success to indicate that we await the followup part
            // Do NOT update any kind of internal state machine, we have not validated what we have received
            reply_success();
            continue;
        }

        command_t cmd = {
            .ins = (command_e) G_received_apdu.ins,
            .rate = G_received_apdu.rate,
            .subcommand = G_received_apdu.subcommand,
            .data =
                {
                    .bytes = G_received_apdu.data,
                    .size = G_received_apdu.data_length,
                },
        };

        if (dispatch_command(&cmd) < 0) {
            // some non recoverable error happened
            return;
        }

        if (G_swap_ctx.state == SIGN_FINISHED) {
            // We are back from an app started in signing mode, our globals are corrupted
            // Force a return to the main function in order to trigger a full clean restart
            return;
        }

        if (G_swap_ctx.state == INITIAL_STATE) {
            ui_idle();
        }
    }
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

__attribute__((section(".boot"))) int main(__attribute__((unused)) int arg0) {
    // exit critical section
    __asm volatile("cpsie i");

    // ensure exception will work as planned
    os_boot();

    for (;;) {
        // Fully reset the global space, as it may be corrupted if we come back from an app started
        // for signing
        PRINTF("Exchange new cycle, reset BSS\n");
        os_explicit_zero_BSS_segment();

        UX_INIT();

        BEGIN_TRY {
            TRY {
                io_seproxyhal_init();

#ifdef TARGET_NANOX
                // grab the current plane mode setting
                G_io_app.plane_mode = os_setting_get(OS_SETTING_PLANEMODE, NULL, 0);
#endif  // TARGET_NANOX

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
            FINALLY {
            }
        }
        END_TRY;
    }
    app_exit();
    return 0;
}
