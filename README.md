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

The `./test` directory contains files for testing the app and its interactions with other apps. Make sure to put up to date binaries in `test/elfs/` before launching the tests.
In a future update, all binaries will be fetched automatically from Github.

For now, only the exchange binary needs to be generated. The following flags are needed for the tests to pass:

```
make TESTING=1 TEST_PUBLIC_KEY=1
```

To run the tests:

```shell script
cd test
yarn install
yarn test
```
