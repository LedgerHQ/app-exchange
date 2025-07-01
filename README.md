# Exchange application

## Introduction

This application is the orchestrator of Swap and Sell functionalities on Ledger devices.

The full documentation of the application and its interactions with other applications is available [here](https://ledgerhq.github.io/app-exchange/)

## Testing

### Ragger tests

The `./test/python` directory contains files for testing the application and its interactions with other applications. It does not contain the binaries used to test the application.

The sideloaded applications binaries need to be generated in their respective repositories and placed in the `tests/python/library_binaries` directory.
The binaries need to be generated with specific flags:

```shell script
make DEBUG=1 TEST_PUBLIC_KEY=1
```

Tests can be run with a command like:

```shell script
pytest -v --tb=short --device nanox -k eth
```
