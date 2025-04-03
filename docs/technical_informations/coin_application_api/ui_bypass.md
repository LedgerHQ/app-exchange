The goal of the Exchange application is to allow the user to perform a fully trusted SWAP through a single screen UI review.

The Exchange application handles the trust checking and the UI, the FROM coin application handles the final payment.
This final payment needs to be validated without UI call **as long as all conditions are strictly met**.

Please refer to the [sequence diagram](../diagram.md) if you want to see the process flow in more details.

The UI bypass on the coin application need to abide by the following rules:

- The bypass is used only when **started by Exchange**.
- The bypass is only used for a single type of **simple transaction**.
- The bypass is only used if the **destination strictly matches**.
- The bypass is only used if the **amount strictly matches**.
- The bypass is only used if the **fees strictly matches**.

If a transaction received in the SWAP context does not match the requirements, it needs to be **rejected** without UI prompt.
The Exchange application will handle the refusal screen display.

Here is an example of the high level detection of the UI bypass.

[`app-solana/src/handle_sign_message.c`](https://github.com/LedgerHQ/app-solana/blob/develop/src/handle_sign_message.c)
```C
--8<-- "docs/deps/app-solana/src/handle_sign_message.c:handle_sign_message_ui"
```

The content of the `check_swap_validity()` function can also be found in the linked file for more information.
