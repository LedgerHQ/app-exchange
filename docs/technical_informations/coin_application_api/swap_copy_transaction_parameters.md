# swap_copy_transaction_parameters()

[`ledger-secure-sdk/lib_standard_app/swap_entrypoints.h`](https://github.com/LedgerHQ/ledger-secure-sdk/tree/master/lib_standard_app/swap_entrypoints.h)
```C
--8<-- "docs/deps/ledger-secure-sdk/lib_standard_app/swap_entrypoints.h:swap_copy_transaction_parameters"
```

[`ledger-secure-sdk/lib_standard_app/swap_lib_calls.h`](https://github.com/LedgerHQ/ledger-secure-sdk/tree/master/lib_standard_app/swap_lib_calls.h)
```C
--8<-- "docs/deps/ledger-secure-sdk/lib_standard_app/swap_lib_calls.h:create_transaction_parameters_t"
```

---

# Example of handle implementation in Solana

[`app-solana/src/swap/handle_swap_sign_transaction.c`](https://github.com/LedgerHQ/app-solana/blob/develop/src/swap/handle_swap_sign_transaction.c)
```C
--8<-- "docs/deps/app-solana/src/swap/handle_swap_sign_transaction.c:copy_transaction_parameters"
```
