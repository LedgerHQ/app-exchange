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
#include "validate_transaction.h"

#include "usbd_core.h"
#define CLA 0xE0

ux_state_t G_ux;
bolos_ux_params_t G_ux_params;

unsigned char G_io_seproxyhal_spi_buffer[IO_SEPROXYHAL_BUFFER_SIZE_B];
swap_app_context_t G_swap_ctx;

void app_main(void) {
    int input_length = 0;

    init_io();

    for (;;) {
        input_length = recv_apdu();
        PRINTF("New APDU received:\n%.*H\n", input_length, G_io_apdu_buffer);
        if (input_length == -1)  // there were an error, lets start from the beginning
            return;
        if (input_length < OFFSET_CDATA || G_io_apdu_buffer[OFFSET_CLA] != CLA) {
            PRINTF("Error: bad APDU\n");
            reply_error(INVALID_INSTRUCTION);
            continue;
        }

        const command_t cmd = {
            .ins = (command_e) G_io_apdu_buffer[OFFSET_INS],
            .rate = G_io_apdu_buffer[OFFSET_P1],
            .subcommand = G_io_apdu_buffer[OFFSET_P2],
            .data =
                {
                    .bytes = G_io_apdu_buffer + OFFSET_CDATA,
                    .size = input_length - OFFSET_CDATA,
                },
        };

        if (dispatch_command(&cmd) < 0) {
            // some non recoverable error happened
            return;
        }

        if (G_swap_ctx.state == SIGN_FINISHED_SUCCESS || G_swap_ctx.state == SIGN_FINISHED_FAIL) {
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

typedef struct previous_cycle_data_s {
    bool had_previous_cycle;
    bool was_successful;
    char appname_last_cycle[BOLOS_APPNAME_MAX_SIZE_B];
} previous_cycle_data_t;

__attribute__((section(".boot"))) int main(__attribute__((unused)) int arg0) {
    // exit critical section
    __asm volatile("cpsie i");

    // previous_cycle_data needs to be on stack to avoid being erased by our init BSS clean
    previous_cycle_data_t previous_cycle_data;
    previous_cycle_data.had_previous_cycle = false;

    // ensure exception will work as planned
    os_boot();

    for (;;) {

        // Before cleaning our BSS, remember if we tried signing and if it worked
        if (G_swap_ctx.state == SIGN_FINISHED_SUCCESS
            || G_swap_ctx.state == SIGN_FINISHED_FAIL) {
            // We save everythin in the stack to avoid erasing it with the BSS reset
            previous_cycle_data.had_previous_cycle = true;
            previous_cycle_data.was_successful = (G_swap_ctx.state == SIGN_FINISHED_SUCCESS);
            memcpy(previous_cycle_data.appname_last_cycle, G_swap_ctx.payin_binary_name, sizeof(previous_cycle_data.appname_last_cycle));

            // Fully reset the global space, as it is was corrupted by the signing app 
            PRINTF("Exchange new cycle, reset BSS\n");
            os_explicit_zero_BSS_segment();
        }

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

#ifdef HAVE_NBGL
                // If last cycle had signing related activities,
                // display it before displaying the main menu.
                // We can't do it earlier because :
                //  - we need to shadow the ui_idle() call
                //  - we need a BSS reset + UX_INIT
                if (previous_cycle_data.had_previous_cycle) {
                    previous_cycle_data.had_previous_cycle = false;
                    if (previous_cycle_data.was_successful) {
                        display_signing_success();
                    } else {
                        display_signing_failure(previous_cycle_data.appname_last_cycle);
                    }
                } else {
                    ui_idle();
                }
#else // HAVE_BAGL
                // No "Ledger Moment" modal, sad
                ui_idle();
#endif

#ifdef HAVE_BLE
                BLE_power(0, NULL);
                BLE_power(1, NULL);
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
