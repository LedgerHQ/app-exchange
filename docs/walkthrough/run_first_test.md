This page provides all the essential setup details to help you get started on enabling the **SWAP** feature in your application.

## Running a first Exchange test

### Clone the Exchange application

Clone the [Exchange application](https://github.com/LedgerHQ/app-exchange).

This application is required for **testing your coin application** but does not need any modifications in the C code.

The **Exchange test framework** is part of this repository, meaning that all swap-related tests for your coin application must be added **inside the Exchange repository**. This structure will change in the future.

### Install Python dependencies

In the Exchange application repository, run the following command to install the required dependencies:  
```sh
pip install -r test/python/requirements.txt
```

### Compile the Exchange application

If using the Ledger VSCode extension, compile the Exchange application using the use_case dbg_use_test_keys. Otherwise, open the `ledger_app.toml` file, check what flags are associated with the aforementioned use case and build Exchange with this flags set. 

### Compile the coin applications

The Exchange test framework requires all swappable coin libraries to be compiled with the correct flags.

Compiling them manually is a **long and error-prone process**, so instead, grab a CI artifact output:

1. Go to the [official test CI](https://github.com/LedgerHQ/app-exchange/actions/workflows/ci-workflow.yml)

2. Download the **artifact** `libraries_binaries.zip` from the **latest successful** run targeting the **develop** branch.

3. Extract the archive in `test/python/lib_binaries/`

Example result
```sh
$> ls test/python/lib_binaries/
APTOS_flex.elf           bitcoin_legacy_nanos.elf     ethereum_classic_stax.elf  solana_nanos.elf    tezos_stax.elf
APTOS_nanos.elf          bitcoin_legacy_nanos2.elf    ethereum_flex.elf          solana_nanos2.elf   ton_flex.elf
APTOS_nanos2.elf         bitcoin_legacy_nanox.elf     ethereum_nanos.elf         solana_nanox.elf    ton_nanos.elf
APTOS_nanox.elf          bitcoin_legacy_stax.elf      ethereum_nanos2.elf        solana_stax.elf     ton_nanos2.elf
APTOS_stax.elf           bitcoin_nanos.elf            ethereum_nanox.elf         stellar_flex.elf    ton_nanox.elf
ATOM_flex.elf            bitcoin_nanos2.elf           ethereum_stax.elf          stellar_nanos.elf   ton_stax.elf
ATOM_nanos.elf           bitcoin_nanox.elf            libraries_binaries.zip     stellar_nanos2.elf  tron_flex.elf
ATOM_nanos2.elf          bitcoin_stax.elf             litecoin_flex.elf          stellar_nanox.elf   tron_nanos.elf
ATOM_nanox.elf           cardano_flex.elf             litecoin_nanos.elf         stellar_stax.elf    tron_nanos2.elf
ATOM_stax.elf            cardano_nanos.elf            litecoin_nanos2.elf        sui_flex.elf        tron_nanox.elf
DOT_flex.elf             cardano_nanos2.elf           litecoin_nanox.elf         sui_nanos2.elf      tron_stax.elf
DOT_nanos.elf            cardano_nanox.elf            litecoin_stax.elf          sui_nanox.elf       xrp_flex.elf
DOT_nanos2.elf           cardano_stax.elf             near_flex.elf              sui_stax.elf        xrp_nanos.elf
DOT_nanox.elf            ethereum_classic_flex.elf    near_nanos2.elf            tezos_flex.elf      xrp_nanos2.elf
DOT_stax.elf             ethereum_classic_nanos.elf   near_nanox.elf             tezos_nanos.elf     xrp_nanox.elf
bitcoin_flex.elf         ethereum_classic_nanos2.elf  near_stax.elf              tezos_nanos2.elf    xrp_stax.elf
bitcoin_legacy_flex.elf  ethereum_classic_nanox.elf   solana_flex.elf            tezos_nanox.elf
```

### Run a simple test

To see all available tests:
```sh
pytest -v --tb=short test/python/ --device all --collect-only
```

To list **only Solana tests for Stax**:
```sh
pytest -v --tb=short test/python/ --device stax --collect-only -k solana
```

To run a specific Solana test for Stax:
```sh
pytest -v --tb=short test/python/ --device stax -k 'test_solana[stax-swap_valid_1]' -s
```

You should remember how to run a single, this will be useful later on.

---

## Next steps

Now you know how to setup and run the Exchange tests, you'll be able to add the tests for your own application and run them as you develop the SWAP feature in your application.
