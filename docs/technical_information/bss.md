When a coin application is started by Exchange through `os_lib_call`, the **BSS section** of the application is not private.  
To save RAM, Exchange shares this memory space with the coin application.  

Because of this design, writing into the BSS at the wrong time can corrupt Exchange’s state.  
Strict rules are enforced to guarantee safety.

## Rules for BSS usage

#### **Forbidden** in:
- `swap_handle_check_address()`
- `swap_handle_get_printable_amount()`

Exchange protects its memory integrity by hashing the BSS section before and after these calls.  
Any modification results in an error being raised.  
Depending on where the application writes, this corruption may or may not be detected.

#### **Allowed** and expected in:
- `swap_copy_transaction_parameters()` (final signing phase)

Exchange is designed to **wipe and reinitialize** memory at this stage, so the BSS can safely be used.

## Consequences of unsafe writes

#### During `CHECK_ADDRESS` or `FORMAT_AMOUNT`: 
- Writing to BSS will trigger an integrity mismatch and return an error.  
- In some cases, writes may go undetected but still lead to undefined behavior later.

#### During `SIGN_TRANSACTION`: 
- Writes are allowed because Exchange performs a full reset of the shared memory afterwards.

## Best practices

- Treat the BSS as **read-only** during `CHECK_ADDRESS` and `FORMAT_AMOUNT`.  
  Do not use global variables, static buffers, or any memory that lives in the BSS section.

- Use the **stack** for temporary values.  
  Handlers in these phases are simple:  
  - `CHECK_ADDRESS` → only validate the provided address.  
  - `FORMAT_AMOUNT` → only format and return the amount string.  
  These operations can be done entirely with stack-based variables.

By following these rules, coin applications remain compatible with Exchange and avoid hard-to-diagnose memory corruption issues.
