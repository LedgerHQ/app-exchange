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

#include "utils.h"
#include "init.h"
#include "menu.h"
#include "swap_app_context.h"
#include "commands.h"
#include "states.h"
#include "get_version_handler.h"
#include "unexpected_command.h"
#include "start_new_transaction.h"
#include "set_partner_key.h"
#include "process_transaction.h"
#include "check_tx_signature.h"
#include "check_payout_address.h"
#include "check_refund_address.h"
#include "apdu_offsets.h"
#include "errors.h"
#include "power_ble.h"
#include "user_validate_amounts.h"

unsigned char G_io_seproxyhal_spi_buffer[IO_SEPROXYHAL_BUFFER_SIZE_B];

#define CLA 0xE0

typedef int (*CommandDispatcher)(swap_app_context_t* ctx, unsigned char* input_buffer, int input_buffer_length, unsigned char* output_buffer, int output_buffer_length);

CommandDispatcher dispatchTable[COMMAND_UPPER_BOUND][STATE_UPPER_BOUND] = {
//                                               INITIAL_STATE          WAITING_TRANSACTION     PROVIDER_SETTED         TRANSACTION_RECIEVED    SIGNATURE_CHECKED       TO_ADDR_CHECKED
/* GET_VERSION_COMMAND                      */  {get_version_handler,   get_version_handler,    get_version_handler,    get_version_handler,    get_version_handler,    get_version_handler},
/* START_NEW_TRANSACTION_COMMAND            */  {start_new_transaction, start_new_transaction,  start_new_transaction,  start_new_transaction,  start_new_transaction,  start_new_transaction},
/* SET_PARTNER_KEY_COMMAND                  */  {unexpected_command,    set_partner_key,        unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command},
/* PROCESS_TRANSACTION_COMMAND              */  {unexpected_command,    unexpected_command,     process_transaction,    unexpected_command,     unexpected_command,     unexpected_command},
/* CHECK_TRANSACTION_SIGNATURE_COMMAND      */  {unexpected_command,    unexpected_command,     unexpected_command,     check_tx_signature,     unexpected_command,     unexpected_command},
/* CHECK_TO_ADDRESS                         */  {unexpected_command,    unexpected_command,     unexpected_command,     unexpected_command,     check_payout_address,   unexpected_command},
/* CHECK_REFUND_ADDRESS                     */  {unexpected_command,    unexpected_command,     unexpected_command,     unexpected_command,     unexpected_command,     check_refund_address}
};

void app_main(void) {
    int output_length = 0;
    int input_length = 0;
    swap_app_context_t ctx;
    init_application_context(&ctx);
    ctx.state = INITIAL_STATE;
    BEGIN_TRY {
        TRY {
            for(;;) {
                input_length = io_exchange(CHANNEL_APDU, output_length);
                if (G_io_apdu_buffer[OFFSET_CLA] != CLA) {
                    THROW(CLASS_NOT_SUPPORTED);
                }
                if (G_io_apdu_buffer[OFFSET_INS] >= COMMAND_UPPER_BOUND) {
                    THROW(INVALID_INSTRUCTION);
                }
                CommandDispatcher handler = PIC(dispatchTable[G_io_apdu_buffer[OFFSET_INS]][ctx.state]);
                output_length = handler(&ctx, G_io_apdu_buffer + OFFSET_CDATA, input_length - OFFSET_CDATA, G_io_apdu_buffer, sizeof(G_io_apdu_buffer));
            }
        } 
        CATCH(EXCEPTION_IO_RESET) {
            THROW(EXCEPTION_IO_RESET);
        }
        FINALLY {}
    }
    END_TRY;
    return;
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
            UX_TICKER_EVENT(G_io_seproxyhal_spi_buffer,
            {
            #ifndef TARGET_NANOX
                if (UX_ALLOWED) {
                    if (ux_step_count) {
                    // prepare next screen
                    ux_step = (ux_step+1)%ux_step_count;
                    // redisplay screen
                    UX_REDISPLAY();
                    }
                }
            #endif // TARGET_NANOX
            });
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

                //ui_idle();
                user_validate_amounts("0.001 BTC", "32.00 ETH", "____");
                user_validate_amounts("0.002 BTC", "64.00 ETH", "____");
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
