"""LIVE-36514: swapping an FA2 token (USDt on Tezos) fails.

Captured from a real failure (Ledger Live Desktop 4.18.0-nightly.20260826023004,
Exchange 4.4.3, Tezos Wallet 3.2.3 on Flex, 2026-08-26):

    => 8004000011 048000002c800006c18000000080000000        INS_SIGN, path
    <= 9000
    => 80048100cf 03<branch> 6c 00<source> d00f a3caa853 df1b 00
                  01fe810959c3d6127a41cbd471e7cb4e91a61b780b00      KT1 USDt contract
                  ff ff08"transfer" 00000069 <michelson params>
    <= 6985                                                   EXC_REJECT

The Exchange leg is a normal SWAP_NG: amount_to_provider 100106851
(100.106851 USDt) and payin address tz1drcp5n9mkJ2eDQQsHBBSDetKJ9s5aKox4.
The Tezos application then rejected the transaction because it compared the
operation against the swap parameters as if it were a native XTZ transfer: a
contract call carries no tez, and its destination is the token contract rather
than the payin address, which lives inside the Michelson parameters.

Fixing this needs both sides:

  * the Tezos application must validate an FA2 `transfer` against the swap
    parameters, which it can only do if it is told which token is being sent;
  * the CAL must publish a sub-coin configuration for FA2 tokens on Tezos -
    ticker and decimals, as it already does for USDT on TON - because the
    Exchange application forwards the sub-coin configuration to the coin
    application and nothing else. Not even the ticker reaches it otherwise.

The tests below cover the fix and what must keep being refused: a swap with no
token configuration, a transfer of a different token than the one quoted, and
the usual tampering with amount, recipient and fees.
"""

import pytest

from hashlib import blake2b, sha256
from base58 import b58encode, b58decode

from ragger.bip import pack_derivation_path
from ragger.error import ExceptionRAPDU
from ragger.utils import create_currency_config

from exchange_client.cal_helper import CurrencyConfiguration
from exchange_client.client import SubCommand
from exchange_client.test_runner import ExchangeTestRunner
from exchange_client.utils import int_to_minimally_sized_bytes

# --------------------------------------------------------------------------- #
# Tezos protocol encoding helpers
# --------------------------------------------------------------------------- #

CLA = 0x80
INS_GET_PUBLIC_KEY = 0x02
INS_SIGN = 0x04
P1_FIRST = 0x00
P1_LAST = 0x81
P2_ED25519 = 0x00

MAGIC_BYTE_UNSAFE = 0x03
OPERATION_TAG_TRANSACTION = 0x6C

STATUS_OK = 0x9000
EXC_REJECT = 0x6985

# KT1XnTn74bUtxHfDtBmm2bGZAQfhPbvKWR8o, "Tether USD" / USDt, 6 decimals.
USDT_CONTRACT_HASH = bytes.fromhex("fe810959c3d6127a41cbd471e7cb4e91a61b780b")
USDT_TOKEN_ID = 0

# KT193D4vozYnhGJQVtw7CoxxqphqUEEwK6Vb, "Quipuswap Governance" / QUIPU. Also
# registered in app/src/parser/fa2_tokens.c, and it has 6 decimals too, so only
# its ticker tells it apart from USDt.
QUIPU_CONTRACT_HASH = bytes.fromhex("05001a8af813094ee8bf162ac2093a8937e8ba83")


def encode_tz1(blake2_hashed_pubkey: bytes) -> str:
    """Base58 encode a 20 byte public key hash as a tz1 address."""
    tz1_prefix = bytes.fromhex("06a19f")
    checksum = sha256(sha256(tz1_prefix + blake2_hashed_pubkey).digest()).digest()[:4]
    return b58encode(tz1_prefix + blake2_hashed_pubkey + checksum).decode()


def decode_tz1(address: str) -> bytes:
    """Extract the 20 byte public key hash out of a tz1 address."""
    raw = b58decode(address)
    return raw[3:-4]


def blake2_hash_pubkey(pubkey: bytes) -> bytes:
    return blake2b(pubkey, digest_size=20).digest()


def zarith(value: int) -> bytes:
    """Unsigned zarith (7 bits per byte, MSB is the continuation bit)."""
    assert value >= 0
    if value == 0:
        return b"\x00"
    out = b""
    while value:
        byte = value & 0x7F
        value >>= 7
        out += bytes([byte | 0x80]) if value else bytes([byte])
    return out


def zarith_signed(value: int) -> bytes:
    """Signed zarith as used by Micheline ints (bit 6 of the first byte is the sign)."""
    negative = value < 0
    value = abs(value)
    first = value & 0x3F
    value >>= 6
    out = bytes([first | (0x40 if negative else 0x00) | (0x80 if value else 0x00)])
    while value:
        byte = value & 0x7F
        value >>= 7
        out += bytes([byte | 0x80]) if value else bytes([byte])
    return out


def micheline_int(value: int) -> bytes:
    return b"\x00" + zarith_signed(value)


def micheline_string(value: str) -> bytes:
    raw = value.encode()
    return b"\x01" + len(raw).to_bytes(4, "big") + raw


def micheline_sequence(payload: bytes) -> bytes:
    return b"\x02" + len(payload).to_bytes(4, "big") + payload


# Micheline "prim with 2 arguments, no annotation" (0x07) applied to Pair (0x07)
MICHELINE_PAIR = b"\x07\x07"


def fa2_transfer_parameters(source: str, destination: str, token_id: int, amount: int) -> bytes:
    """Build the parameters of an FA2 `transfer` entrypoint call.

    Pair(from_, [Pair(to_, Pair(token_id, amount))]) - byte for byte what
    Ledger Live sent in the captured failure.
    """
    transfer = MICHELINE_PAIR + micheline_string(destination) \
        + MICHELINE_PAIR + micheline_int(token_id) + micheline_int(amount)
    return micheline_sequence(MICHELINE_PAIR + micheline_string(source)
                              + micheline_sequence(transfer))


# --------------------------------------------------------------------------- #
# Currency configuration
# --------------------------------------------------------------------------- #

XTZ_PACKED_DERIVATION_PATH = pack_derivation_path("m/44'/1729'/0'")

# The configuration the CAL must publish for an FA2 token: the sub-coin
# configuration carries the ticker and the decimals, which is what reaches the
# coin application. Same shape as USDT on TON.
USDT_XTZ_CURRENCY_CONFIGURATION = CurrencyConfiguration(
    ticker="USDt",
    conf=create_currency_config("USDt", "Tezos", ("USDt", 6)),
    packed_derivation_path=XTZ_PACKED_DERIVATION_PATH,
)

# Exactly what the CAL sends for USDt on Tezos today: ticker "USDt",
# application "Tezos", and NO sub-coin configuration - so the application is
# given neither ticker nor decimals to validate against.
USDT_XTZ_NO_TOKEN_CONFIGURATION = CurrencyConfiguration(
    ticker="USDt",
    conf=create_currency_config("USDt", "Tezos"),
    packed_derivation_path=XTZ_PACKED_DERIVATION_PATH,
)

# The payout leg of the captured failure was ETH. It is irrelevant to the bug,
# which is entirely on the FROM side, so we pay out to XTZ instead: that keeps
# the tests running with the Tezos application as the only sideloaded library.
XTZ_CURRENCY_CONFIGURATION = CurrencyConfiguration(
    ticker="XTZ",
    conf=create_currency_config("XTZ", "Tezos"),
    packed_derivation_path=XTZ_PACKED_DERIVATION_PATH,
)


class TezosFa2Tests(ExchangeTestRunner):
    """Swap FROM an FA2 token held on Tezos."""

    currency_configuration = USDT_XTZ_CURRENCY_CONFIGURATION

    # The token the final transaction actually transfers. Overridden by the
    # subclass that transfers a token other than the one being swapped.
    token_contract_hash = USDT_CONTRACT_HASH
    token_id = USDT_TOKEN_ID

    # Payin address of the swap provider, i.e. the FA2 `to_` of the transfer.
    valid_destination_1 = "tz1drcp5n9mkJ2eDQQsHBBSDetKJ9s5aKox4"
    valid_destination_2 = "tz1TNKZitanSzHmkxVRriDdMU7qrQukae9Yr"

    # Address of the Speculos device on XTZ_PACKED_DERIVATION_PATH. It is both
    # the refund address of the swap and the FA2 `from_` of the transfer.
    valid_refund = "tz1YPjCVqgimTAPmxZX9egDeTFRCmrTRqmp9"

    # 100.106851 USDt, the amount of the captured failure.
    valid_send_amount_1 = 100106851
    valid_send_amount_2 = 446739662
    # Operation fee, in mutez. The captured failure used 2000.
    valid_fees_1 = 2000
    valid_fees_2 = 10078

    fake_refund = "abcdabcd"
    fake_payout = "abcdabcd"

    signature_refusal_error_code = EXC_REJECT

    def perform_valid_swap_from_custom(self, destination, send_amount, fees,
                                       destination_memo, refund_address=None,
                                       refund_memo=None, ui_validation=True,
                                       allow_alias=True, start_application=True):
        """Same as the base class, but paying out to XTZ instead of ETH."""
        tx_infos = {
            "payin_address": destination,
            "payin_extra_id": destination_memo,
            "refund_address": self.valid_refund if refund_address is None else refund_address,
            "refund_extra_id": "",
            "payout_address": self.valid_refund,
            "payout_extra_id": "",
            "currency_from": self.currency_configuration.ticker,
            "currency_to": XTZ_CURRENCY_CONFIGURATION.ticker,
            "amount_to_provider": int_to_minimally_sized_bytes(send_amount),
            "amount_to_wallet": b"\246\333t\233+\330\000",
        }
        self._perform_valid_exchange(subcommand=SubCommand.SWAP_NG,
                                     tx_infos=tx_infos,
                                     from_currency_configuration=self.currency_configuration,
                                     to_currency_configuration=XTZ_CURRENCY_CONFIGURATION,
                                     fees=fees,
                                     ui_validation=ui_validation,
                                     start_application=start_application)

    def perform_final_tx(self, destination, send_amount, fees, memo):
        """Sign an FA2 `transfer` of `send_amount` tokens to `destination`."""
        backend = self.backend

        rapdu = backend.exchange(CLA, INS_GET_PUBLIC_KEY, P1_FIRST, P2_ED25519,
                                 XTZ_PACKED_DERIVATION_PATH)
        assert rapdu.status == STATUS_OK
        source_hash = blake2_hash_pubkey(rapdu.data[2:])
        source = encode_tz1(source_hash)
        assert source == self.valid_refund, \
            f"Unexpected device address {source}, expected {self.valid_refund}"

        rapdu = backend.exchange(CLA, INS_SIGN, P1_FIRST, P2_ED25519,
                                 XTZ_PACKED_DERIVATION_PATH)
        assert rapdu.status == STATUS_OK

        payload = self._craft_fa2_transfer(source, source_hash, destination,
                                           send_amount, fees)
        # A non-9000 answer raises, so the tampering tests below can expect it.
        backend.exchange(CLA, INS_SIGN, P1_LAST, P2_ED25519, data=payload)

    def _craft_fa2_transfer(self, source: str, source_hash: bytes,
                            destination: str, send_amount: int,
                            fees: int) -> bytes:
        payload = bytes([MAGIC_BYTE_UNSAFE])
        payload += bytes(32)                              # branch, not checked
        payload += bytes([OPERATION_TAG_TRANSACTION])
        payload += b"\x00" + source_hash                  # implicit tz1 source
        payload += zarith(fees)
        payload += zarith(174728483)                      # counter
        payload += zarith(3551)                           # gas limit
        payload += zarith(0)                              # storage limit
        # A contract call carries no tez.
        payload += zarith(0)
        # Destination is the FA2 token contract, not the swap payin address.
        payload += b"\x01" + self.token_contract_hash + b"\x00"
        payload += b"\xff"                                # parameters present
        payload += b"\xff" + bytes([len("transfer")]) + b"transfer"
        parameters = fa2_transfer_parameters(source, destination,
                                             self.token_id, send_amount)
        payload += len(parameters).to_bytes(4, "big") + parameters
        return payload

    # The standard swap flow, with an FA2 token transfer as the final
    # transaction instead of a native XTZ transfer.
    def perform_test_swap_fa2_valid_1(self):
        self.perform_valid_swap_from_custom(self.valid_destination_1,
                                            self.valid_send_amount_1,
                                            self.valid_fees_1,
                                            "")
        try:
            self.perform_coin_specific_final_tx(self.valid_destination_1,
                                                self.valid_send_amount_1,
                                                self.valid_fees_1,
                                                "")
        except ExceptionRAPDU as e:
            pytest.fail(
                f"LIVE-36514: the Tezos application refused to sign the FA2 "
                f"token transfer with SW 0x{e.status:04x}. The operation "
                f"moves {self.valid_send_amount_1} units of USDt to "
                f"{self.valid_destination_1}, both taken from the Michelson "
                f"parameters, and carries 0 mutez.")
        self.assert_exchange_is_started()

    # A transfer of a token other than the one the swap was quoted for must be
    # refused, even though that token is itself known to the application.
    def perform_test_swap_fa2_wrong_token(self):
        self.perform_valid_swap_from_custom(self.valid_destination_1,
                                            self.valid_send_amount_1,
                                            self.valid_fees_1,
                                            "")
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1,
                                                self.valid_send_amount_1,
                                                self.valid_fees_1,
                                                "")
        assert e.value.status == self.signature_refusal_error_code
        self.assert_exchange_is_started()


class TezosFa2WrongTokenTests(TezosFa2Tests):
    """Swap quoted for USDt, but the operation transfers QUIPU instead.

    Both tokens are in the application registry and both have 6 decimals, so
    only the ticker from the coin configuration tells them apart.
    """

    token_contract_hash = QUIPU_CONTRACT_HASH


class TezosFa2NoTokenConfigTests(TezosFa2Tests):
    """The situation in production: the CAL sends no sub-coin configuration.

    The application is then told nothing about the token, so it cannot check
    that the operation moves the token the swap was quoted for. Refusing is
    the only safe answer, and this test pins it down.
    """

    currency_configuration = USDT_XTZ_NO_TOKEN_CONFIGURATION

    def perform_test_swap_fa2_no_config(self):
        self.perform_valid_swap_from_custom(self.valid_destination_1,
                                            self.valid_send_amount_1,
                                            self.valid_fees_1,
                                            "")
        with pytest.raises(ExceptionRAPDU) as e:
            self.perform_coin_specific_final_tx(self.valid_destination_1,
                                                self.valid_send_amount_1,
                                                self.valid_fees_1,
                                                "")
        assert e.value.status == self.signature_refusal_error_code
        self.assert_exchange_is_started()


class TezosNativeSwapTests(TezosFa2Tests):
    """Control case: the very same flow, with a native XTZ transfer.

    It shares everything with TezosFa2Tests except the final transaction, so a
    failure here means the test setup is broken rather than the application.
    """

    currency_configuration = XTZ_CURRENCY_CONFIGURATION
    valid_send_amount_1 = 10000000

    def perform_final_tx(self, destination, send_amount, fees, memo):
        backend = self.backend

        rapdu = backend.exchange(CLA, INS_GET_PUBLIC_KEY, P1_FIRST, P2_ED25519,
                                 XTZ_PACKED_DERIVATION_PATH)
        assert rapdu.status == STATUS_OK
        source_hash = blake2_hash_pubkey(rapdu.data[2:])

        rapdu = backend.exchange(CLA, INS_SIGN, P1_FIRST, P2_ED25519,
                                 XTZ_PACKED_DERIVATION_PATH)
        assert rapdu.status == STATUS_OK

        payload = bytes([MAGIC_BYTE_UNSAFE])
        payload += bytes(32)
        payload += bytes([OPERATION_TAG_TRANSACTION])
        payload += b"\x00" + source_hash
        payload += zarith(fees)
        payload += zarith(174728483)
        payload += zarith(3551)
        payload += zarith(0)
        payload += zarith(send_amount)
        payload += b"\x00\x00" + decode_tz1(destination)   # implicit tz1
        payload += b"\x00"                                 # no parameters

        backend.exchange(CLA, INS_SIGN, P1_LAST, P2_ED25519, data=payload)

    def perform_test_swap_native_valid_1(self):
        self.perform_valid_swap_from_custom(self.valid_destination_1,
                                            self.valid_send_amount_1,
                                            self.valid_fees_1,
                                            "")
        self.perform_coin_specific_final_tx(self.valid_destination_1,
                                            self.valid_send_amount_1,
                                            self.valid_fees_1,
                                            "")
        self.assert_exchange_is_started()


# Use a class to reuse the same Speculos instance
class TestsTezosFa2:

    @pytest.mark.parametrize("test_to_run", ["swap_native_valid_1"])
    def test_tezos_native_swap_control(self, backend, exchange_navigation_helper,
                                       test_to_run):
        """Sanity check: a native XTZ swap goes through with this exact setup."""
        TezosNativeSwapTests(backend, exchange_navigation_helper).run_test(test_to_run)

    @pytest.mark.parametrize("test_to_run", ["swap_fa2_valid_1"])
    def test_tezos_fa2(self, backend, exchange_navigation_helper, test_to_run):
        """LIVE-36514: a swap paying with USDt must be signed."""
        TezosFa2Tests(backend, exchange_navigation_helper).run_test(test_to_run)

    @pytest.mark.parametrize("test_to_run",
                             ["swap_wrong_amount", "swap_wrong_destination",
                              "swap_wrong_fees"])
    def test_tezos_fa2_tampered(self, backend, exchange_navigation_helper,
                                test_to_run):
        """A tampered FA2 transfer must not be signed."""
        TezosFa2Tests(backend, exchange_navigation_helper).run_test(test_to_run)

    @pytest.mark.parametrize("test_to_run", ["swap_fa2_wrong_token"])
    def test_tezos_fa2_wrong_token(self, backend, exchange_navigation_helper,
                                   test_to_run):
        """Transferring another registered token must not be signed."""
        TezosFa2WrongTokenTests(backend,
                                exchange_navigation_helper).run_test(test_to_run)

    @pytest.mark.parametrize("test_to_run", ["swap_fa2_no_config"])
    def test_tezos_fa2_without_token_config(self, backend,
                                            exchange_navigation_helper,
                                            test_to_run):
        """An FA2 swap with no sub-coin configuration must stay refused."""
        TezosFa2NoTokenConfigTests(backend,
                                   exchange_navigation_helper).run_test(test_to_run)
