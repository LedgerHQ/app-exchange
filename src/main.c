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
#include "io_helpers.h"
#include "menu.h"
#include "globals.h"
#include "commands.h"
#include "command_dispatcher.h"
#include "apdu_offsets.h"
#include "swap_errors.h"
#include "apdu_parser.h"
#include "sign_result.h"
#include "get_challenge_handler.h"

#include "usbd_core.h"

// Error code thrown by os_lib_call when the requested application is not installed
// Defined in SDK for old API_LEVELs, but not on recent API_LEVELs
#ifndef SWO_SEC_APP_14
#define SWO_SEC_APP_14 0x5114  // (ERR_SEC_APP + ERR_GEN_ID_14)
#endif

// Simple global variable to access the stack variable defined in main
swap_app_context_t *G_swap_ctx;

#ifdef HAVE_NBGL
// On nbgl, remember some data from the previous cycle if applicable to display a status screen
typedef struct previous_cycle_data_s {
    bool had_previous_cycle;
    bool was_successful;
    char appname_last_cycle[BOLOS_APPNAME_MAX_SIZE_B + 1];
} previous_cycle_data_t;
#endif

void app_main(void) {
    int input_length = 0;
    command_t cmd;

    io_init();

    for (;;) {
        input_length = io_recv_command();
        PRINTF("New APDU received:\n%.*H\n", input_length, G_io_apdu_buffer);
        // there was a fatal error during APDU reception, restart from the beginning
        // Don't bother trying to send a status code, IOs are probably out
        if (input_length == -1) {
            explicit_bzero(G_swap_ctx, sizeof(*G_swap_ctx));
            return;
        }

        uint16_t ret = check_apdu_validity(G_io_apdu_buffer, input_length, &cmd);
        if (ret != 0) {
            PRINTF("Sending early reply 0x%4x\n", ret);
            reply_error(ret);
            continue;
        }

        if (dispatch_command(&cmd) < 0) {
            // some non recoverable error happened
            explicit_bzero(G_swap_ctx, sizeof(*G_swap_ctx));
            return;
        }

        if (G_swap_ctx->state == SIGN_SUCCESS || G_swap_ctx->state == SIGN_FAILURE) {
            // We are back from an app started in signing mode, our globals are corrupted
            // Force a return to the main function in order to trigger a full clean restart
            return;
        }
    }
}

__attribute__((section(".boot"))) int main(__attribute__((unused)) int arg0) {
    // exit critical section
    __asm volatile("cpsie i");

    // ensure exception will work as planned
    os_boot();

    // Global like variable, placed in stack to avoid BSS corruption by the library application
    swap_app_context_t swap_ctx;
    G_swap_ctx = &swap_ctx;
    explicit_bzero(G_swap_ctx, sizeof(*G_swap_ctx));

    // On NBGL, remember some data from the previous cycle if applicable to display a status screen
#ifdef HAVE_NBGL
    previous_cycle_data_t previous_cycle_data;
    explicit_bzero(&previous_cycle_data, sizeof(previous_cycle_data));
#endif

    for (;;) {
        // If we are back from a lib app in signing mode, clean our BSS
        if (G_swap_ctx->state == SIGN_SUCCESS || G_swap_ctx->state == SIGN_FAILURE) {
#ifdef HAVE_NBGL
            // And save some data for the status screen
            previous_cycle_data.had_previous_cycle = true;
            strlcpy(previous_cycle_data.appname_last_cycle,
                    G_swap_ctx->payin_binary_name,
                    sizeof(previous_cycle_data.appname_last_cycle));
            previous_cycle_data.was_successful = (G_swap_ctx->state == SIGN_SUCCESS);
#endif

            // Fully reset the global space, as it is was corrupted by the signing app
            PRINTF("Exchange new cycle, reset BSS\n");
            explicit_bzero(G_swap_ctx, sizeof(*G_swap_ctx));
            os_explicit_zero_BSS_segment();
            G_swap_ctx = &swap_ctx;
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
                        PRINTF("Displaying modal for successful last cycle\n");
                        display_signing_success();
                    } else {
                        PRINTF("Displaying modal for failed last cycle\n");
                        display_signing_failure(previous_cycle_data.appname_last_cycle);
                    }
                } else {
                    ui_idle();
                }
#else  // HAVE_BAGL
       // No "Ledger Moment" modal, sad
                ui_idle();
#endif

#ifdef HAVE_BLE
                BLE_power(0, NULL);
                BLE_power(1, NULL);
#endif

                // to prevent it from having a fixed value at boot
                roll_challenge();

                app_main();
            }
            CATCH(SWO_SEC_APP_14) {
                // We have called os_lib_call for an application that is not installed.
                // Inform the caller of this failure and fully reset the context
                // We don't try to handle this kind of error
                PRINTF("Fatal: os_lib_call has thrown SWO_SEC_APP_14\n");
                instant_reply_error(APPLICATION_NOT_INSTALLED);
                CLOSE_TRY;
                continue;
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
    os_sched_exit(-1);
    return 0;
}
