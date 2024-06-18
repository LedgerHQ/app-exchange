/*****************************************************************************
 *   Ledger App Exchange.
 *   (c) 2024 Ledger SAS.
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
#include "io.h"
#include "io_helpers.h"
#include "swap_errors.h"

int reply_error(swap_error_e error) {
    return io_send_response_buffers(NULL, 0, error);
}

int instant_reply_error(swap_error_e error) {
    G_io_apdu_buffer[0] = (error >> 8) & 0xFF;
    G_io_apdu_buffer[1] = error & 0xFF;
    return io_exchange(CHANNEL_APDU | IO_RETURN_AFTER_TX, 2);
}

int reply_success(void) {
    return reply_error(SUCCESS);
}

int instant_reply_success(void) {
    return instant_reply_error(SUCCESS);
}
