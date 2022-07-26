from dataclasses import dataclass
from pathlib import Path

import pytest

from ragger import Firmware
from ragger.backend import SpeculosBackend, LedgerCommBackend, LedgerWalletBackend

from .apps.exchange import ERRORS


@dataclass(frozen=True)
class Application:
    path: Path
    firmware: Firmware

APPLICATION_DIRECTORY = (Path(__file__).parent.parent / "elfs").resolve()
APPLICATIONS = {"bitcoin": "Bitcoin",
                "ethereum": "Ethereum",
                "tezos": "Tezos",
                "stellar": "Stellar",
                "xrp": "RXP",
                "litecoin": "Litecoin"}
BACKENDS = ["speculos", "ledgercomm", "ledgerwallet"]
EXCHANGES = [
    Application(APPLICATION_DIRECTORY / 'exchange_nanos.elf',
                Firmware('nanos', '2.1')),
    Application(APPLICATION_DIRECTORY / 'exchange_nanox.elf',
                Firmware('nanox', '2.0.2')),
    Application(APPLICATION_DIRECTORY / 'exchange_nanosp.elf',
                Firmware('nanosp', '1.0.3'))
]

@pytest.fixture(params=EXCHANGES)
def exchange(request):
    return request.param

def prepare_speculos_args(exchange):
    current_device = exchange.firmware.device
    assert APPLICATION_DIRECTORY.is_dir(), \
        f"{APPLICATION_DIRECTORY} is not a directory"
    application = None
    speculos_args = ["--model", current_device, "--sdk", exchange.firmware.version]
    original_size = len(speculos_args)
    for application_elf in [a for a in APPLICATION_DIRECTORY.iterdir()
                            if a.name.endswith(".elf") and f"{current_device}." in a.name]:
        for k, v in APPLICATIONS.items():
            if k in application_elf.name:
                speculos_args.append(f"-l{v}:{application_elf}")
                break
    application = exchange.path
    assert exchange.path.is_file(), f"{exchange.path} must exist"
    assert len(speculos_args) == original_size + len(APPLICATIONS), \
        f"Speculos argument number mismatch, some application elf may be missing!"
    return ([application], {"args": speculos_args})

def pytest_addoption(parser):
    parser.addoption("--backend", action="store", default="speculos")


@pytest.fixture(scope="session")
def backend(pytestconfig):
    return pytestconfig.getoption("backend")


def create_backend(backend: bool, exchange: Application, raises: bool = True):
    if backend.lower() == "ledgercomm":
        return LedgerCommBackend(exchange.firmware, interface="hid", raises=raises, errors=ERRORS)
    elif backend.lower() == "ledgerwallet":
        return LedgerWalletBackend(exchange.firmware, errors=ERRORS)
    elif backend.lower() == "speculos":
        args, kwargs = prepare_speculos_args(exchange)
        return SpeculosBackend(*args, exchange.firmware, **kwargs, raises=raises, errors=ERRORS)
    else:
        raise ValueError(f"Backend '{backend}' is unknown. Valid backends are: {BACKENDS}")


@pytest.fixture
def client(backend, exchange):
    with create_backend(backend, exchange) as b:
        yield b


@pytest.fixture
def client_no_raise(backend, exchange):
    with create_backend(backend, exchange, raises=False) as b:
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
