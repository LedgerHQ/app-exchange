from dataclasses import dataclass
from pathlib import Path
import pytest

from ragger import Firmware
from ragger.backend import SpeculosBackend, LedgerCommBackend, LedgerWalletBackend

from .apps.exchange import ERRORS
from .utils import app_path_from_app_name

def __str__(self):        # also tried __repr__()
        # Attempt to print the 'select' attribute in "pytest -v" output
        return self.select


APPS_DIRECTORY = (Path(__file__).parent.parent / "elfs").resolve()

EXCHANGE_APP="exchange"

SIDELOADED_APPS = {"bitcoin": "Bitcoin",
                "ethereum": "Ethereum",
                "tezos": "Tezos",
                "stellar": "Stellar",
                "xrp": "RXP",
                "litecoin": "Litecoin"}

BACKENDS = ["speculos", "ledgercomm", "ledgerwallet"]

FIRMWARES = [Firmware('nanos', '2.1'),
             Firmware('nanox', '2.0.2'),
             Firmware('nanosp', '1.0.3')]

def pytest_addoption(parser):
    parser.addoption("--backend", action="store", default="speculos")
    # Enable ussing --'device' in the pytest command line to restrict testing to specific devices
    for fw in FIRMWARES:
        parser.addoption("--"+fw.device, action="store_true", help="run on nanos only")


# Glue to call every test that depends on the firmware once for each required firmware
def pytest_generate_tests(metafunc):
    if "firmware" in metafunc.fixturenames:
        fw_list = []
        ids = []
        # First pass: enable only demanded firmwares
        for fw in FIRMWARES:
            if metafunc.config.getoption(fw.device):
                fw_list.append(fw)
                ids.append(fw.device + " " + fw.version)
        # Second pass if no specific firmware demanded: add them all
        if not fw_list:
            for fw in FIRMWARES:
                fw_list.append(fw)
                ids.append(fw.device + " " + fw.version)
        metafunc.parametrize("firmware", fw_list, ids=ids)

def prepare_speculos_args(firmware):
    speculos_args = ["--model", firmware.device, "--sdk", firmware.version]

    # Add "-l Appname:filepath" to Speculos command line for every required app
    for filename, appname in SIDELOADED_APPS.items():
        app_path = app_path_from_app_name(APPS_DIRECTORY, filename, firmware.device)
        speculos_args.append(f"-l{appname}:{app_path}")

    # Compute Exchange App binary
    exchange_app_path = app_path_from_app_name(APPS_DIRECTORY, EXCHANGE_APP, firmware.device)

    return ([exchange_app_path], {"args": speculos_args})


@pytest.fixture(scope="session")
def backend(pytestconfig):
    return pytestconfig.getoption("backend")


def create_backend(backend: bool, firmware: Firmware, raises: bool = True):
    if backend.lower() == "ledgercomm":
        return LedgerCommBackend(firmware, interface="hid", raises=raises, errors=ERRORS)
    elif backend.lower() == "ledgerwallet":
        return LedgerWalletBackend(firmware, errors=ERRORS)
    elif backend.lower() == "speculos":
        args, kwargs = prepare_speculos_args(firmware)
        return SpeculosBackend(*args, firmware, **kwargs, raises=raises, errors=ERRORS)
    else:
        raise ValueError(f"Backend '{backend}' is unknown. Valid backends are: {BACKENDS}")

@pytest.fixture
def client(backend, firmware):
    with create_backend(backend, firmware) as b:
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
