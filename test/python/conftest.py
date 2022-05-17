from pathlib import Path

import pytest

from ragger.backend import SpeculosBackend, LedgerCommBackend, LedgerWalletBackend


APPLICATION_DIRECTORY = (Path(__file__).parent.parent / "elfs").resolve()
APPLICATIONS = {"bitcoin": "Bitcoin",
                "ethereum": "Ethereum",
                "tezos": "Tezos",
                "stellar": "Stellar",
                "xrp": "RXP",
                "litecoin": "Litecoin"}
BACKENDS = ["speculos", "ledgercomm", "ledgerwallet"]


def prepare_speculos_args():
    assert APPLICATION_DIRECTORY.is_dir(), \
        f"{APPLICATION_DIRECTORY} is not a directory"
    application = None
    speculos_args = ["--model", "nanos", "--sdk", "2.1"]
    for application_elf in [a for a in APPLICATION_DIRECTORY.iterdir()
                            if a.name.endswith(".elf") and "nanos." in a.name]:
        for k, v in APPLICATIONS.items():
            if k in application_elf.name:
                speculos_args.append(f"-l{v}:{application_elf}")
                break
        if "exchange" in application_elf.name:
            application = str(application_elf)
    assert application is not None, \
        f"{application} not found"
    assert len(speculos_args) == 4 + len(APPLICATIONS)
    return ([application], {"args": speculos_args})

def pytest_addoption(parser):
    parser.addoption("--backend", action="store", default="speculos")


@pytest.fixture(scope="session")
def backend(pytestconfig):
    return pytestconfig.getoption("backend")


def create_backend(backend: bool, raises: bool = True):
    if backend.lower() == "ledgercomm":
        return LedgerCommBackend(interface="hid", raises=raises)
    elif backend.lower() == "ledgerwallet":
        return LedgerWalletBackend()
    elif backend.lower() == "speculos":
        args, kwargs = prepare_speculos_args()
        return SpeculosBackend(*args, **kwargs, raises=raises)
    else:
        raise ValueError(f"Backend '{backend}' is unknown. Valid backends are: {BACKENDS}")


@pytest.fixture
def client(backend):
    with create_backend(backend) as b:
        yield b


@pytest.fixture
def client_no_raise(backend):
    with create_backend(backend, raises=False) as b:
        yield b


@pytest.fixture(autouse=True)
def use_only_on_backend(request, backend):
    if request.node.get_closest_marker('use_on_backend'):
        current_backend = request.node.get_closest_marker('use_on_backend').args[0]
        if current_backend != backend:
            pytest.skip('skipped on this backend: {}'.format(current_backend))

def pytest_configure(config):
  config.addinivalue_line(
        "markers", "use_only_on_backend(backend): skip test if not on the specified backend",
  )
