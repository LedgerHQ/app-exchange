# Exchange app for the Ledger Nano S and Ledger Nano X

## Introduction

This app is the orchestrator of Swap and Sell functionalities on ledger devices.
An overview of the feature is available [here](https://blog.ledger.com/secure-swap/)

## Building and installing

To build and install the app on your Nano S or X you must set up the Ledger Nano S or X build environments. Please follow the Getting Started instructions at the [Ledger Nano S github repository](https://github.com/LedgerHQ/ledger-nano-s).

The command to compile and load the app onto the device is:

```shell script
make load
```

To remove the app from the device do:

```shell script
make delete
```

## Testing

The `./test` directory contains files for testing the app and its interactions with other apps. It does not contain the binaries used to test the app.
The binaries need to be generated and put in `test/elfs/` before launching the tests.

The exchange binaries need to be generated with the following flags.

```
make TESTING=1 TEST_PUBLIC_KEY=1
```

Then the application must be placed in the `test/elfs/` directory, under the name `exchange_nanos.elf`, `exchange_nanox.elf`, or `exchange_nanosp.elf` depending on the SDK:

```
// Choose one
// cp bin/app.elf test/elfs/exchange_nanos.elf
// cp bin/app.elf test/elfs/exchange_nanox.elf
// cp bin/app.elf test/elfs/exchange_nanosp.elf
```

The sideloaded applications binaries need to be generated in their respective repositories and placed in the `test/elfs/` directory.
For the entire test collection to pass, the following binaries must be present
```
bitcoin_nanos.elf
bitcoin_nanosp.elf
bitcoin_nanox.elf
ethereum_nanos.elf
ethereum_nanosp.elf
ethereum_nanosp.elf
ethereum_nanox.elf
litecoin_nanos.elf
litecoin_nanosp.elf
litecoin_nanox.elf
stellar_nanos.elf
stellar_nanosp.elf
stellar_nanox.elf
tezos_legacy_nanos.elf
tezos_legacy_nanosp.elf
tezos_legacy_nanox.elf
tezos_new_nanos.elf
tezos_new_nanosp.elf
tezos_new_nanox.elf
xrp_nanos.elf
xrp_nanosp.elf
xrp_nanox.elf
```

To run the tests:

```shell script
cd test
yarn install
yarn test
```
