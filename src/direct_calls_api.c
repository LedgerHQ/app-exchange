#ifdef DIRECT_CALLS_API

#include "direct_calls_api.h"
#include "currency_lib_calls.h"
#include "globals.h"
#include "io_helpers.h"
#include "validate_transaction.h"
#include "check_addresses_and_amounts.h"

int direct_check_address(const command_t *cmd) {
    PRINTF("direct_check_address\n");

    // Read the address from the apdu
    uint16_t offset = 0;
    buf_t address_to_check;
    if (!parse_to_sized_buffer(cmd->data.bytes, cmd->data.size, 1, &address_to_check, &offset)) {
        PRINTF("!parse_to_sized_buffer address_to_check\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }
    // NULL terminate the address
    char address_to_check_str[sizeof(G_swap_ctx.swap_transaction.payin_address)] = {0};
    memcpy(address_to_check_str, address_to_check.bytes, address_to_check.size);

    // Shift address from input apdu
    buf_t cmd_without_address;
    cmd_without_address.size = cmd->data.size - offset;
    cmd_without_address.bytes = cmd->data.bytes + offset;

    buf_t address_parameters;
    buf_t ticker;
    buf_t sub_coin_config;
    char application_name[BOLOS_APPNAME_MAX_SIZE_B + 1];
    uint16_t ret = parse_check_address(cmd_without_address,
                                       &address_parameters,
                                       &ticker,
                                       &application_name,
                                       &sub_coin_config);
    if (ret != 0) {
        PRINTF("Error: parse_check_address failed\n");
        return reply_error(ret);
    }

    // os_lib_call wrapper
    PRINTF("sub_coin_config = %.*H\n", sub_coin_config.size, sub_coin_config.bytes);
    PRINTF("address_parameters = %.*H\n", address_parameters.size, address_parameters.bytes);
    PRINTF("address_to_check = '%s'\n", address_to_check_str);
    PRINTF("application_name = '%s'\n", application_name);
    ret = check_address(&sub_coin_config,
                        &address_parameters,
                        application_name,
                        address_to_check_str,
                        NULL);

    if (ret != 0) {
        PRINTF("Error: check_address failed\n");
        return reply_error(ret);
    }

    return reply_success();
}

int direct_format_amount(const command_t *cmd) {
    PRINTF("direct_format_amount\n");

    // Read the address from the apdu
    uint16_t offset = 0;
    buf_t amount;
    if (!parse_to_sized_buffer(cmd->data.bytes, cmd->data.size, 1, &amount, &offset)) {
        PRINTF("!parse_to_sized_buffer amount\n");
        return reply_error(INCORRECT_COMMAND_DATA);
    }

    // Shift amount from input apdu
    buf_t cmd_without_address;
    cmd_without_address.size = cmd->data.size - offset;
    cmd_without_address.bytes = cmd->data.bytes + offset;

    buf_t address_parameters;
    buf_t ticker;
    buf_t sub_coin_config;
    char application_name[BOLOS_APPNAME_MAX_SIZE_B + 1];
    uint16_t ret = parse_check_address(cmd_without_address,
                                       &address_parameters,
                                       &ticker,
                                       &application_name,
                                       &sub_coin_config);
    if (ret != 0) {
        PRINTF("Error: parse_check_address failed\n");
        return reply_error(ret);
    }

    // os_lib_call wrapper
    PRINTF("sub_coin_config = %.*H\n", sub_coin_config.size, sub_coin_config.bytes);
    PRINTF("address_parameters = %.*H\n", address_parameters.size, address_parameters.bytes);
    PRINTF("amount = '%.*H'\n", amount.size, amount.bytes);
    PRINTF("application_name = '%s'\n", application_name);
    char to_print[sizeof(G_swap_ctx.printable_send_amount)] = {0};
    ret = get_printable_amount(&sub_coin_config,
                               application_name,
                               amount.bytes,
                               amount.size,
                               to_print,
                               sizeof(to_print),
                               false);
    if (ret != 0) {
        PRINTF("Error: check_address failed\n");
        return reply_error(ret);
    }
    char to_print_as_fees[sizeof(G_swap_ctx.printable_send_amount)] = {0};
    ret = get_printable_amount(&sub_coin_config,
                               application_name,
                               amount.bytes,
                               amount.size,
                               to_print_as_fees,
                               sizeof(to_print_as_fees),
                               false);
    if (ret != 0) {
        PRINTF("Error: check_address failed\n");
        return reply_error(ret);
    }

    direct_amount_review(application_name, to_print, to_print_as_fees);
    return 0;
}

#endif  // DIRECT_CHECK_ADDRESS
