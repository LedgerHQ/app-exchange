import pytest
from pathlib import Path

from speculos.client import SpeculosClient
from ragger.bip import pack_derivation_path
from ragger.conftest import configuration as ragger_conf

from exchange_client.test_runner import ExchangeTestRunner, SWAP_TESTS_EXCEPT_THORSWAP
from apps.xrp import XRP_DEFAULT_PATH, XRP_PUBKEY_SIZE, XRPClient, RippleErrors
from apps import cal as cal


# Paths whose device-derived XRP addresses are used as the source-of-truth refund
# and arbitrary destinations in the swap tests.
_XRP_TEST_PATHS = {
    "dest1": XRP_DEFAULT_PATH,
    "dest2": "m/44'/144'/0'/0'/1",
}

# Sidecar Speculos port. Picked far from 5000 to avoid clashing with the main
# test backend.
_SIDECAR_API_PORT = 5055


def _query_xrp_pubkey_and_address(client: SpeculosClient, path: str):
    response = client.apdu_exchange(cla=0xE0, ins=0x02, p1=0, p2=0x40,
                                    data=pack_derivation_path(path))
    pubkey = bytes(response[1:1 + XRP_PUBKEY_SIZE])
    addr_len = response[1 + XRP_PUBKEY_SIZE]
    addr_start = 2 + XRP_PUBKEY_SIZE
    return pubkey, response[addr_start:addr_start + addr_len].decode()


@pytest.fixture(scope="session")
def xrp_addresses(firmware, cli_user_seed):
    """Spawn a sidecar Speculos running XRP standalone and query the (pubkey, address)
    pairs we need before the main Speculos has dispatched into XRP. Cached for the session."""
    device = firmware.device
    if firmware.device == "nanosp" :
        device = "nanos2"
    xrp_elf = Path(__file__).parent / "lib_binaries" / f"xrp_{device}.elf"

    args = ["--model", firmware.device, "--api-port", str(_SIDECAR_API_PORT)]
    seed = cli_user_seed or ragger_conf.OPTIONAL.CUSTOM_SEED
    if seed:
        args += ["--seed", seed]

    with SpeculosClient(str(xrp_elf), args=args,
                        api_url=f"http://127.0.0.1:{_SIDECAR_API_PORT}") as client:
        return {label: _query_xrp_pubkey_and_address(client, path)
                for label, path in _XRP_TEST_PATHS.items()}


class RippleTests(ExchangeTestRunner):
    currency_configuration = cal.XRP_CURRENCY_CONFIGURATION
    valid_destination_memo_1 = "0"
    valid_destination_memo_2 = "123"
    valid_refund_memo = ""
    valid_send_amount_1 = 1000000
    valid_send_amount_2 = 446739662
    valid_fees_1 = 100
    valid_fees_2 = 10078
    fake_refund = "abcdabcd"
    fake_refund_memo = ""
    fake_payout = "abcdabcd"
    fake_payout_memo = ""
    signature_refusal_error_code = RippleErrors.SW_SWAP_CHECKING_FAIL

    def __init__(self, backend, exchange_navigation_helper, xrp_addresses):
        super().__init__(backend, exchange_navigation_helper)
        self.valid_destination_1_pubkey, self.valid_destination_1 = xrp_addresses["dest1"]
        self.valid_refund_pubkey, self.valid_refund = xrp_addresses["dest1"]
        _, self.valid_destination_2 = xrp_addresses["dest2"]

    def perform_final_tx(self, destination, send_amount, fees, memo):
        XRPClient(self.backend).send_simple_sign_tx(path=XRP_DEFAULT_PATH,
                                                    source_pubkey=self.valid_destination_1_pubkey,
                                                    source_address=self.valid_destination_1,
                                                    fees=fees,
                                                    memo=memo,
                                                    destination=destination,
                                                    send_amount=send_amount)

        # TODO : assert signature validity


# Use a class to reuse the same Speculos instance
class TestsRipple:

    @pytest.mark.parametrize('test_to_run', SWAP_TESTS_EXCEPT_THORSWAP)
    def test_ripple(self, backend, exchange_navigation_helper, xrp_addresses, test_to_run):
        RippleTests(backend, exchange_navigation_helper, xrp_addresses).run_test(test_to_run)
