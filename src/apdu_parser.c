/*****************************************************************************
 *   Ledger
 *   (c) 2023 Ledger
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
#include "apdu_parser.h"

// Keep as global the received fields of the command
// We need to remember them in case we receive a split command
typedef struct apdu_s {
    bool expecting_more;
    uint8_t instruction;
    uint8_t rate;
    uint8_t subcommand;
    uint16_t data_length;
    uint8_t raw_transaction[256 * 2];
} apdu_t;
apdu_t G_received_apdu;

// Dedicated function for instruction checking as it's self contained
static uint16_t check_instruction(uint8_t instruction, uint8_t subcommand) {
    // True if the instruction is part of a flow and the context must be checked
    bool check_subcommand_context = false;
    // True if the instruction can be received between user approval and child lib start
    bool allowed_during_waiting_for_signing = false;
    // {STATE} if this command is only accepted at a specific state, -1 otherwise
    int check_current_state = -1;

    if ((instruction == CHECK_ASSET_IN_AND_DISPLAY || instruction == CHECK_ASSET_IN_NO_DISPLAY) &&
        (subcommand == SWAP || subcommand == SWAP_NG)) {
        PRINTF("Instruction CHECK_ASSET_IN_AND_DISPLAY is only for SELL and FUND based flows\n");
        return INVALID_INSTRUCTION;
    }

    if (instruction == CHECK_PAYOUT_ADDRESS && (subcommand != SWAP && subcommand != SWAP_NG)) {
        PRINTF("Instruction CHECK_PAYOUT_ADDRESS is only for SWAP based flows\n");
        return INVALID_INSTRUCTION;
    }

    if (instruction == GET_CHALLENGE && (subcommand != SWAP && subcommand != SWAP_NG)) {
        PRINTF("Instruction GET_CHALLENGE is only for SWAP based flows\n");
        return INVALID_INSTRUCTION;
    }

    if (instruction == SEND_TRUSTED_NAME_DESCRIPTOR &&
        (subcommand != SWAP && subcommand != SWAP_NG)) {
        PRINTF("Instruction SEND_TRUSTED_NAME_DESCRIPTOR is only for SWAP based flows\n");
        return INVALID_INSTRUCTION;
    }

    if ((instruction == CHECK_REFUND_ADDRESS_AND_DISPLAY ||
         instruction == CHECK_REFUND_ADDRESS_NO_DISPLAY) &&
        (subcommand != SWAP && subcommand != SWAP_NG)) {
        PRINTF("Instruction CHECK_REFUND_ADDRESS_X is only for SWAP based flows\n");
        return INVALID_INSTRUCTION;
    }

    switch (instruction) {
        case GET_VERSION_COMMAND:
            // We ignore the current context for this command as it doesn't modify anything
            check_subcommand_context = false;
            // No strict dependency on the current state as long as it is not a protected state
            // (WAITING_USER_VALIDATION and WAITING_SIGNING)
            check_current_state = -1;
            break;
        case START_NEW_TRANSACTION_COMMAND:
            // We can always restart a new transaction
            allowed_during_waiting_for_signing = true;
            check_subcommand_context = false;
            check_current_state = -1;
            break;
        case SET_PARTNER_KEY_COMMAND:
            check_current_state = WAITING_TRANSACTION;
            check_subcommand_context = true;
            break;
        case CHECK_PARTNER_COMMAND:
            check_current_state = PROVIDER_SET;
            check_subcommand_context = true;
            break;
        case PROCESS_TRANSACTION_RESPONSE_COMMAND:
            check_current_state = PROVIDER_CHECKED;
            check_subcommand_context = true;
            break;
        case CHECK_TRANSACTION_SIGNATURE_COMMAND:
            check_current_state = TRANSACTION_RECEIVED;
            check_subcommand_context = true;
            break;
        case GET_CHALLENGE:
            check_current_state = SIGNATURE_CHECKED;
            check_subcommand_context = true;
            break;
        case SEND_TRUSTED_NAME_DESCRIPTOR:
            check_current_state = SIGNATURE_CHECKED;
            check_subcommand_context = true;
            break;
        case CHECK_PAYOUT_ADDRESS:
        case CHECK_ASSET_IN_AND_DISPLAY:
        case CHECK_ASSET_IN_NO_DISPLAY:
            check_current_state = SIGNATURE_CHECKED;
            check_subcommand_context = true;
            break;
        case CHECK_REFUND_ADDRESS_AND_DISPLAY:
        case CHECK_REFUND_ADDRESS_NO_DISPLAY:
            check_current_state = PAYOUT_ADDRESS_CHECKED;
            check_subcommand_context = true;
            break;
        case PROMPT_UI_DISPLAY:
            check_current_state = ALL_ADDRESSES_CHECKED;
            check_subcommand_context = true;
            break;
        case START_SIGNING_TRANSACTION:
            check_current_state = WAITING_SIGNING;
            allowed_during_waiting_for_signing = true;
            check_subcommand_context = true;
            break;
        default:
            PRINTF("Received unknown instruction %d\n", instruction);
            return INVALID_INSTRUCTION;
    }

    if (G_swap_ctx.state == WAITING_USER_VALIDATION) {
        PRINTF("Refuse all APDUs during UI display\n");
        return UNEXPECTED_INSTRUCTION;
    }

    if (!allowed_during_waiting_for_signing && G_swap_ctx.state == WAITING_SIGNING) {
        PRINTF("Received instruction %d, not allowed during WAITING_SIGNING state\n", instruction);
        return UNEXPECTED_INSTRUCTION;
    }

    if (check_subcommand_context && subcommand != G_swap_ctx.subcommand) {
        PRINTF("Received subcommand %d, current flow uses %d\n", subcommand, G_swap_ctx.subcommand);
        return UNEXPECTED_INSTRUCTION;
    }

    if (check_current_state != -1 && G_swap_ctx.state != check_current_state) {
        PRINTF("Received instruction %d requiring state %d, but current state is %d\n",
               instruction,
               check_current_state,
               G_swap_ctx.state);
        return UNEXPECTED_INSTRUCTION;
    }

    return 0;
}

// Return 0 if we can proceed with this APDU, return a status code if we can not
uint16_t check_apdu_validity(uint8_t *apdu, size_t apdu_length, command_t *command) {
    if (apdu_length < OFFSET_CDATA) {
        PRINTF("Error: malformed APDU, length is too short %d\n", apdu_length);
        return MALFORMED_APDU;
    }

    uint8_t data_length = apdu[OFFSET_LC];
    if (data_length != apdu_length - OFFSET_CDATA) {
        PRINTF("Error: malformed APDU, recv %d bytes, claiming %d header bytes and %d data bytes\n",
               apdu_length,
               OFFSET_CDATA,
               data_length);
        return MALFORMED_APDU;
    }

    if (apdu[OFFSET_CLA] != CLA) {
        PRINTF("Error: invalid CLA %d\n", apdu[OFFSET_CLA]);
        return CLASS_NOT_SUPPORTED;
    }

    // Get rate from P1
    uint8_t rate = apdu[OFFSET_P1];
    if (rate != FIXED && rate != FLOATING) {
        PRINTF("Incorrect P1 %d\n", rate);
        return WRONG_P1;
    }

    // Extract subcommand from P2
    uint8_t subcommand = apdu[OFFSET_P2] & SUBCOMMAND_MASK;
    if (subcommand != SWAP && subcommand != SELL && subcommand != FUND && subcommand != SWAP_NG &&
        subcommand != SELL_NG && subcommand != FUND_NG) {
        PRINTF("Incorrect subcommand %d\n", subcommand);
        return WRONG_P2_SUBCOMMAND;
    }

    // Get instruction and ensure it makes sense in the current context
    uint8_t instruction = apdu[OFFSET_INS];
    // CHECK_ASSET_IN_LEGACY_AND_DISPLAY shares the same value as CHECK_PAYOUT_ADDRESS which is
    // inconvenient. Replace this with the new CHECK_ASSET_IN_AND_DISPLAY for legacy flows. New
    // flows must use CHECK_ASSET_IN_AND_DISPLAY directly.
    if (instruction == CHECK_ASSET_IN_LEGACY_AND_DISPLAY &&
        (subcommand == SELL || subcommand == FUND)) {
        PRINTF("Replacing legacy value for CHECK_ASSET_IN_AND_DISPLAY instruction\n");
        instruction = CHECK_ASSET_IN_AND_DISPLAY;
    }
    uint16_t err = check_instruction(instruction, subcommand);
    if (err != 0) {
        return err;
    }

    // Extract extension from P2
    uint8_t extension = apdu[OFFSET_P2] & EXTENSION_MASK;
    if ((extension & ~(P2_NONE | P2_MORE | P2_EXTEND)) != 0) {
        PRINTF("Incorrect extension %d\n", extension);
        return WRONG_P2_EXTENSION;
    }

    bool is_first_data_chunk = !(extension & P2_EXTEND);
    bool is_last_data_chunk = !(extension & P2_MORE);
    bool is_whole_apdu = is_first_data_chunk && is_last_data_chunk;
    // Split reception is only for NG flows
    if (subcommand != SWAP_NG && subcommand != SELL_NG && subcommand != FUND_NG && !is_whole_apdu) {
        PRINTF("Extension %d refused, only allowed for unified flows\n", extension);
        return WRONG_P2_EXTENSION;
    }
    // Split reception is only for PROCESS_TRANSACTION_RESPONSE_COMMAND
    if (instruction != PROCESS_TRANSACTION_RESPONSE_COMMAND &&
        instruction != SEND_TRUSTED_NAME_DESCRIPTOR && !is_whole_apdu) {
        PRINTF("Extension %d refused for instruction %d\n", extension, instruction);
        return WRONG_P2_EXTENSION;
    }

    if (is_first_data_chunk) {
        G_received_apdu.instruction = instruction;
        G_received_apdu.rate = rate;
        G_received_apdu.subcommand = subcommand;
        G_received_apdu.data_length = data_length;
        if (!is_last_data_chunk) {
            memcpy(G_received_apdu.raw_transaction, apdu + OFFSET_CDATA, data_length);
            G_received_apdu.expecting_more = true;
        }
    } else {
        // The command received claims to extend a previously received one. Check if it's expected
        if (!G_received_apdu.expecting_more) {
            PRINTF("Previous command did not indicate a followup\n");
            return INVALID_P2_EXTENSION;
        }
        // Also ensure they are the same kind
        if (G_received_apdu.instruction != instruction || G_received_apdu.rate != rate ||
            G_received_apdu.subcommand != subcommand) {
            PRINTF("Refusing to extend a different apdu, exp (%d, %d, %d), recv (%d, %d, %d)\n",
                   G_received_apdu.instruction,
                   G_received_apdu.rate,
                   G_received_apdu.subcommand,
                   instruction,
                   rate,
                   subcommand);
            return INVALID_P2_EXTENSION;
        }
        if (G_received_apdu.data_length + data_length > sizeof(G_received_apdu.raw_transaction)) {
            PRINTF("Reception buffer size %d is not sufficient to receive more data (%d + %d)\n",
                   sizeof(G_received_apdu.raw_transaction),
                   G_received_apdu.data_length,
                   data_length);
            return INVALID_P2_EXTENSION;
        }
        // Extend the already received buffer
        memcpy(G_received_apdu.raw_transaction + G_received_apdu.data_length,
               apdu + OFFSET_CDATA,
               data_length);
        G_received_apdu.data_length += data_length;
    }

    if (!is_last_data_chunk) {
        // Reply a blank success to indicate that we await the followup part
        // Do NOT update any kind of internal state machine, we have not validated what we have
        // received
        PRINTF("Split APDU reception in progress, current size %d\n", G_received_apdu.data_length);
        return SUCCESS;
    } else {
        // The APDU is valid and complete, signal caller that it can proceed
        command->ins = G_received_apdu.instruction;
        command->rate = G_received_apdu.rate;
        command->subcommand = G_received_apdu.subcommand;
        command->data.size = G_received_apdu.data_length;
        // Reset chunks reception
        G_received_apdu.expecting_more = false;
        if (is_whole_apdu) {
            // No split has taken place, data is still in the APDU reception buffer
            command->data.bytes = apdu + OFFSET_CDATA;
        } else {
            // Split has taken place, data is in the split buffer
            PRINTF("Split APDU successfully recreated, size %d\n", G_received_apdu.data_length);
            command->data.bytes = G_received_apdu.raw_transaction;
        }
        return 0;
    }
}
