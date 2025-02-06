from enum import IntEnum
from ragger.utils import create_currency_config, RAPDU
from ragger.bip import pack_derivation_path
from typing import List, Optional

APTOS_CONF = create_currency_config("APT", "Aptos")
APTOS_DERIVATION_PATH = "m/44'/637'/0'"
APTOS_PACKED_DERIVATION_PATH = pack_derivation_path(APTOS_DERIVATION_PATH)

MAX_APDU_LEN: int = 255

CLA: int = 0x5B

class P1(IntEnum):
    # Parameter 1 for first APDU number.
    P1_START = 0x00
    # Parameter 1 for maximum APDU number.
    P1_MAX   = 0x03
    # Parameter 1 for screen confirmation for GET_PUBLIC_KEY.
    P1_CONFIRM = 0x01

class P2(IntEnum):
    # Parameter 2 for last APDU to receive.
    P2_LAST = 0x00
    # Parameter 2 for more APDU to receive.
    P2_MORE = 0x80

class InsType(IntEnum):
    GET_VERSION    = 0x03
    GET_APP_NAME   = 0x04
    GET_PUBLIC_KEY = 0x05
    SIGN_TX        = 0x06

class Errors(IntEnum):
    SW_DENY                    = 0x6985
    SW_WRONG_P1P2              = 0x6A86
    SW_WRONG_DATA_LENGTH       = 0x6A87
    SW_INS_NOT_SUPPORTED       = 0x6D00
    SW_CLA_NOT_SUPPORTED       = 0x6E00
    SW_WRONG_RESPONSE_LENGTH   = 0xB000
    SW_DISPLAY_BIP32_PATH_FAIL = 0xB001
    SW_DISPLAY_ADDRESS_FAIL    = 0xB002
    SW_DISPLAY_AMOUNT_FAIL     = 0xB003
    SW_WRONG_TX_LENGTH         = 0xB004
    SW_TX_PARSING_FAIL         = 0xB005
    SW_GET_PUB_KEY_FAIL        = 0xB006
    SW_BAD_STATE               = 0xB007
    SW_SIGNATURE_FAIL          = 0xB008
    SW_DISPLAY_GAS_FEE_FAIL    = 0xB009
    SW_SWAP_CHECKING_FAIL      = 0xB00A


def split_message(message: bytes, max_size: int) -> List[bytes]:
    return [message[x:x + max_size] for x in range(0, len(message), max_size)]


# As copied from the Nano App tester
class AptosCommandSender:
    def __init__(self, backend) -> None:
        self.backend = backend

    def sign_tx(self, send_amount : int, destination : str) -> List[RAPDU]:
        # Base and trail apdu for Aptos, builds a transaction by concatenating them
        # ex: base_apdu + dest_1 + middle_apdu + amount_1 + trail_apdu
        base_apdu = "b5e97db07fa0bd0e5598aa3643a9bc6f6693bddc1a9fec9e674a461eaa00b193783135e8b00430253a22ba041d860c373d7a1501ccf7ac2d1ad37a8ed2775aee000000000000000002000000000000000000000000000000000000000000000000000000000000000104636f696e087472616e73666572010700000000000000000000000000000000000000000000000000000000000000010a6170746f735f636f696e094170746f73436f696e000220";
        middle_apdu = "08"
        trail_apdu = "00000000204e0000000000006400000000000000565c51630000000022"
        

        
        built_apdu = base_apdu + destination + middle_apdu + send_amount.to_bytes(4,'little').hex() + trail_apdu
        transaction = bytes.fromhex(built_apdu)

        packed_path = APTOS_PACKED_DERIVATION_PATH
        self.backend.exchange(cla=CLA,
                              ins=InsType.SIGN_TX,
                              p1=P1.P1_START,
                              p2=P2.P2_MORE,
                              data=packed_path)
        messages = split_message(transaction, MAX_APDU_LEN)
        idx: int = P1.P1_START + 1

        for msg in messages[:-1]:
            self.backend.exchange(cla=CLA,
                                  ins=InsType.SIGN_TX,
                                  p1=idx,
                                  p2=P2.P2_MORE,
                                  data=msg)
            idx += 1

        with self.backend.exchange_async(cla=CLA,
                                         ins=InsType.SIGN_TX,
                                         p1=idx,
                                         p2=P2.P2_LAST,
                                         data=messages[-1]) as response:
            return response

    def get_async_response(self) -> Optional[RAPDU]:
        return self.backend.last_async_response

