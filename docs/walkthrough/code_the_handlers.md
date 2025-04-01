## Code the handlers to make the first tests pass

The next step is to code the two first handlers to make the tests `swap_ui_only` and `swap_wrong_refund` pass with success

### Test `swap_ui_only`

This test stops before sending the `START_SIGNING_TRANSACTION` APDU.
This means that no coin signature takes place, the only handlers called are [`swap_handle_check_address()`](../technical_informations/coin_application_api/swap_handle_check_address.md) and [`swap_handle_get_printable_amount()`](../technical_informations/coin_application_api/swap_handle_get_printable_amount.md).

You can use this test to validate that:

- `swap_handle_check_address()` correctly recognizes the `valid_destination_1` address.
- `swap_handle_get_printable_amount()` correctly formats the amount on screen.

Don't forget to run ragger with the `--golden_run` option when creating / updating the snapshots.

### Test `swap_wrong_refund`

This test sends an address that does not belong to the device as refund address.

You can use this test to validate that `swap_handle_check_address()` correctly refuses to recognize the `fake_refund` address.

## Code the last handler and the UI bypass

You can now code the [`swap_copy_transaction_parameters()`](../technical_informations/coin_application_api/swap_copy_transaction_parameters.md) handler.

You can now also code the UI bypass in the transaction signature.

Please refer to the [UI bypass documentation](../technical_informations/coin_application_api/ui_bypass.md) carefully.

All tests should now pass.
