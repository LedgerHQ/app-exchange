#include "io_utils.h"
#include "os.h"
#include "cx.h"
#include "utils.h"
#include "sol/string_utils.h"
#include "sol/parser.h"
#include "sol/transaction_summary.h"
#include "globals.h"
#include "apdu.h"
#include "handle_sign_offchain_message.h"
#include "ui_api.h"

// ensure the command buffer has space to append a NUL terminal
CASSERT(MAX_OFFCHAIN_MESSAGE_LENGTH < MAX_MESSAGE_LENGTH, global_h);

void ui_application_domain(const OffchainMessageHeader *header) {
    const uint8_t empty_application_domain[OFFCHAIN_MESSAGE_APPLICATION_DOMAIN_LENGTH] = {
        OFFCHAIN_EMPTY_APPLICATION_DOMAIN};

    // Check if application domain buffer contains only zeroes
    if (memcmp(header->application_domain,
               empty_application_domain,
               OFFCHAIN_MESSAGE_APPLICATION_DOMAIN_LENGTH) == 0) {
        // Application buffer contains only zeroes - displaying base58 encoded string not needed
        summary_item_set_string(transaction_summary_general_item(),
                                "Application",
                                "Domain not provided");
    } else {
        summary_item_set_offchain_message_application_domain(transaction_summary_general_item(),
                                                             "Application",
                                                             header->application_domain);
    }
}

// To reduce unnecessary
// preprocessor directives and keep the function cleaner, I explicitly suppress
// warnings about unused `parser`.
void ui_general(const OffchainMessageHeader *header,
                const bool is_ascii,
                const size_t signer_index,
                Parser *parser __attribute__((unused))) {
    if (N_storage.settings.display_mode == DisplayModeExpert) {
        SummaryItem *item = transaction_summary_primary_or_general_item();
        // First signer
        summary_item_set_pubkey(item, "Signer", &header->signers[signer_index]);

        if (header->signers_length > 1) {
            summary_item_set_u64(transaction_summary_general_item(),
                                 "Other signers",
                                 header->signers_length);
        }

        ui_application_domain(header);

        summary_item_set_u64(transaction_summary_general_item(), "Version", header->version);
        summary_item_set_u64(transaction_summary_general_item(), "Format", header->format);
        summary_item_set_u64(transaction_summary_general_item(), "Size", header->length);
        summary_item_set_hash(transaction_summary_general_item(), "Hash", &G_command.message_hash);
    } else if (!is_ascii) {
        summary_item_set_hash(transaction_summary_primary_or_general_item(),
                              "Hash",
                              &G_command.message_hash);
    }
}

void setup_ui(const OffchainMessageHeader *header,
              const bool is_ascii,
              Parser *parser,
              const size_t signer_index) {
    // fill out UI steps
    transaction_summary_reset();

    ui_general(header, is_ascii, signer_index, parser);

    enum SummaryItemKind summary_step_kinds[MAX_TRANSACTION_SUMMARY_ITEMS];
    size_t num_summary_steps = 0;
    if (transaction_summary_finalize(summary_step_kinds, &num_summary_steps) > 1) {
        // We can ignore missing primary item in this case
        THROW(ApduReplySolanaSummaryFinalizeFailed);
    }
    start_sign_offchain_message_ui(is_ascii, num_summary_steps);
}

void handle_sign_offchain_message(volatile unsigned int *flags, volatile unsigned int *tx) {
    if (!tx || G_command.instruction != InsSignOffchainMessage ||
        G_command.state != ApduStatePayloadComplete) {
        THROW(ApduReplySdkInvalidParameter);
    }

    if (G_command.non_confirm) {
        // Uncomment this to allow unattended signing.
        //*tx = set_result_sign_message();
        // THROW(ApduReplySuccess);
        UNUSED(tx);
        THROW(ApduReplySdkNotSupported);
    }

    if (G_command.message_length > MAX_OFFCHAIN_MESSAGE_LENGTH) {
        THROW(ApduReplySolanaInvalidMessageSize);
    }

    // parse header
    Parser parser = {G_command.message, G_command.message_length};
    OffchainMessageHeader header;
    Pubkey public_key;

    if (parse_offchain_message_header(&parser, &header)) {
        THROW(ApduReplySolanaInvalidMessageHeader);
    }

    // validate message
    if (header.version != 0 || header.format > 1 || header.length == 0 ||
        header.length != parser.buffer_length || header.signers_length == 0) {
        THROW(ApduReplySolanaInvalidMessageHeader);
    }

    get_public_key(public_key.data, G_command.derivation_path, G_command.derivation_path_length);

    // assert that the requested signer exists in the signers list
    size_t signer_index;
    if (get_pubkey_index(&public_key, header.signers, header.signers_length, &signer_index) != 0) {
        THROW(ApduReplySolanaInvalidMessageHeader);
    }

    const bool is_ascii = is_data_ascii(parser.buffer, parser.buffer_length);
    const bool is_utf8 = is_ascii ? true : is_data_utf8(parser.buffer, parser.buffer_length);

    if ((!is_ascii && header.format != 1) || !is_utf8) {
        // Message has invalid header version or is not valid utf8 string
        THROW(ApduReplySolanaInvalidMessageFormat);
    } else if (!is_ascii && N_storage.settings.allow_blind_sign != BlindSignEnabled) {
        // UTF-8 messages are allowed only with blind sign enabled
        THROW(ApduReplySdkNotSupported);
    }

    // compute message hash if needed
    if (!is_ascii || N_storage.settings.display_mode == DisplayModeExpert) {
        cx_hash_sha256(parser.buffer,  // Only message content is hashed
                       header.length,
                       (uint8_t *) &G_command.message_hash,
                       HASH_LENGTH);
    }

    setup_ui(&header, is_ascii, &parser, signer_index);

    *flags |= IO_ASYNCH_REPLY;
}
