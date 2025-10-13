## Code the handlers to make the first tests pass

The next step is to implement the first two handlers so that the tests `swap_ui_only` and `swap_wrong_refund` pass.

### Test `swap_ui_only`

This test stops before sending the `START_SIGNING_TRANSACTION` APDU. That means no coin signature takes place; the only handlers called are [`swap_handle_check_address()`](../technical_information/coin_application_api/swap_handle_check_address.md) and [`swap_handle_get_printable_amount()`](../technical_information/coin_application_api/swap_handle_get_printable_amount.md).

You can use this test to validate that:

- `swap_handle_check_address()` correctly recognizes the `valid_destination_1` address.
- `swap_handle_get_printable_amount()` correctly formats the amount for display.

Don't forget to run ragger with the `--golden_run` option when creating or updating the snapshots.

### Test `swap_wrong_refund`

This test sends a refund address that does not belong to the device.

You can use this test to validate that `swap_handle_check_address()` correctly rejects the `fake_refund` address.

## Code the last handler and the UI bypass

You can now implement the [`swap_copy_transaction_parameters()`](../technical_information/coin_application_api/swap_copy_transaction_parameters.md) handler.

You can also implement the UI bypass for the final transaction signature.

Please refer to the [UI bypass documentation](../technical_information/coin_application_api/ui_bypass.md) carefully.

Please refer to the [Coin application error codes](../technical_information/coin_application_api/error_codes.md) to learn how to handle a refusal of the final transaction.

All tests should now pass.
