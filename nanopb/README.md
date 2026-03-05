# nanopb — Ledger-patched version

This folder contains a Ledger-specific patched version of [nanopb](https://github.com/nanopb/nanopb) **0.3.9**, a lightweight Protocol Buffers implementation for embedded systems.

## Contents

| Path | Description |
|---|---|
| `nanopb-0.3.9/` | nanopb 0.3.9 sources with the Ledger patch already applied |
| `patch_nanopb_0.3.9.diff` | The patch to apply on top of a vanilla nanopb 0.3.9 release |

## What the patch changes

The patch adapts nanopb for the Ledger Nano S hardware environment:

- **`PIC()` macro wrapping** — All accesses to field descriptor tables (`pb_field_t`) are wrapped with the `PIC()` macro. This is required on Ledger devices because the firmware runs from flash (ROM) and data pointers must go through position-independent code indirection.
- **Ledger OS integration** — Adds `#include "os.h"` to pull in the Ledger SDK.
- **`PB_FIELD_32BIT` enabled** — Enables 32-bit field width support, needed for the message sizes used in Exchange.
- **`nanopb_generator.py` fix** — Replaces the deprecated `"rU"` file open mode with `"r"` for Python 3 compatibility.
- **Stack overflow detection** (debug) — Adds instrumentation helpers (`check_stack_overflow`, `__cyg_profile_func_enter/exit`) to assist with debugging stack usage on constrained devices. These are compiled in only when `-finstrument-functions` is set.

## How to regenerate the patched sources

If you need to apply the patch to a fresh nanopb 0.3.9 download:

```bash
# Download and extract vanilla nanopb 0.3.9
tar -xzf nanopb-nanopb-0.3.9.tar.gz

# Apply the Ledger patch
cd nanopb-nanopb-0.3.9
patch -p1 < ../nanopb/patch_nanopb_0.3.9.diff
```

## How to regenerate the patch

If you make changes to the sources and need to update the patch, generate it by diffing against the vanilla release:

```bash
diff -ruN nanopb-nanopb-0.3.9/ nanopb/nanopb-0.3.9/ \
  --exclude='*.pyc' --exclude='.git' \
  > nanopb/patch_nanopb_0.3.9.diff
```