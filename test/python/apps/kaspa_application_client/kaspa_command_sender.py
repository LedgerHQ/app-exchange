from enum import IntEnum
from typing import Generator, List, Optional
from contextlib import contextmanager

from ragger.backend.interface import BackendInterface, RAPDU
from ragger.bip import pack_derivation_path

from .kaspa_transaction import Transaction


MAX_APDU_LEN: int = 255

CLA: int = 0xE0

class P1(IntEnum):
    # Parameter 1 for first APDU number.
    P1_START = 0x00
    P1_OUTPUTS = 0x01
    P1_INPUTS = 0x02
    P1_NEXT_SIGNATURE = 0x03
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
    SIGN_MESSAGE   = 0x07

class Errors(IntEnum):
    SW_DENY                       = 0x6985
    SW_WRONG_P1P2                 = 0x6A86
    SW_WRONG_DATA_LENGTH          = 0x6A87
    SW_INS_NOT_SUPPORTED          = 0x6D00
    SW_CLA_NOT_SUPPORTED          = 0x6E00
    SW_WRONG_RESPONSE_LENGTH      = 0xB000
    SW_DISPLAY_BIP32_PATH_FAIL    = 0xB001
    SW_DISPLAY_ADDRESS_FAIL       = 0xB002
    SW_DISPLAY_AMOUNT_FAIL        = 0xB003
    SW_WRONG_TX_LENGTH            = 0xB004
    SW_TX_PARSING_FAIL            = 0xB005
    SW_TX_HASH_FAIL               = 0xB006
    SW_BAD_STATE                  = 0xB007
    SW_SIGNATURE_FAIL             = 0xB008
    SW_WRONG_BIP32_PURPOSE        = 0xB009
    SW_WRONG_BIP32_COIN_TYPE      = 0xB00A
    SW_WRONG_BIP32_PATH_LEN       = 0xB00B
    SW_MESSAGE_PARSING_FAIL       = 0xB010
    SW_MESSAGE_TOO_LONG           = 0xB011
    SW_MESSAGE_TOO_SHORT          = 0xB012
    SW_MESSAGE_ADDRESS_TYPE_FAIL  = 0xB013
    SW_MESSAGE_ADDRESS_INDEX_FAIL = 0xB014
    SW_MESSAGE_LEN_PARSING_FAIL   = 0xB015
    SW_MESSAGE_UNEXPECTED         = 0xB016
    SW_SWAP_WRONG_FEES            = 0xC000
    SW_SWAP_WRONG_AMOUNT          = 0xC000
    SW_SWAP_WRONG_ADDRESS         = 0xC000

def split_message(message: bytes, max_size: int) -> List[bytes]:
    return [message[x:x + max_size] for x in range(0, len(message), max_size)]

class KaspaCommandSender:
    def __init__(self, backend: BackendInterface) -> None:
        self.backend = backend


    def get_app_and_version(self) -> RAPDU:
        return self.backend.exchange(cla=0xB0,  # specific CLA for BOLOS
                                     ins=0x01,  # specific INS for get_app_and_version
                                     p1=P1.P1_START,
                                     p2=P2.P2_LAST,
                                     data=b"")


    def get_version(self) -> RAPDU:
        return self.backend.exchange(cla=CLA,
                                     ins=InsType.GET_VERSION,
                                     p1=P1.P1_START,
                                     p2=P2.P2_LAST,
                                     data=b"")


    def get_app_name(self) -> RAPDU:
        return self.backend.exchange(cla=CLA,
                                     ins=InsType.GET_APP_NAME,
                                     p1=P1.P1_START,
                                     p2=P2.P2_LAST,
                                     data=b"")


    def get_public_key(self, path: str) -> RAPDU:
        return self.backend.exchange(cla=CLA,
                                     ins=InsType.GET_PUBLIC_KEY,
                                     p1=P1.P1_START,
                                     p2=P2.P2_LAST,
                                     data=pack_derivation_path(path))


    @contextmanager
    def get_public_key_with_confirmation(self, path: str) -> Generator[None, None, None]:
        with self.backend.exchange_async(cla=CLA,
                                         ins=InsType.GET_PUBLIC_KEY,
                                         p1=P1.P1_CONFIRM,
                                         p2=P2.P2_LAST,
                                         data=pack_derivation_path(path)) as response:
            yield response


    @contextmanager
    def sign_tx(self, transaction: Transaction) -> Generator[None, None, None]:
        self.backend.exchange(cla=CLA,
                              ins=InsType.SIGN_TX,
                              p1=P1.P1_START,
                              p2=P2.P2_MORE,
                              data=transaction.serialize_first_chunk())

        for txoutput in transaction.outputs:
            self.backend.exchange(cla=CLA,
                                  ins=InsType.SIGN_TX,
                                  p1=P1.P1_OUTPUTS,
                                  p2=P2.P2_MORE,
                                  data=txoutput.serialize())

        txinput = None # used again after the loop for the last value
        for i, txinput in enumerate(transaction.inputs):
            if i < len(transaction.inputs) - 1:
                self.backend.exchange(cla=CLA,
                                    ins=InsType.SIGN_TX,
                                    p1=P1.P1_INPUTS,
                                    p2=P2.P2_MORE,
                                    data=txinput.serialize())

        # Last input, we'll end here
        with self.backend.exchange_async(cla=CLA,
                                    ins=InsType.SIGN_TX,
                                    p1=P1.P1_INPUTS,
                                    p2=P2.P2_LAST,
                                    data=txinput.serialize()) as response:

            yield response

    def get_next_signature(self) -> RAPDU:
        return self.backend.exchange(cla=CLA,
                                    ins=InsType.SIGN_TX,
                                    p1=P1.P1_NEXT_SIGNATURE,
                                    p2=P2.P2_LAST)

    def get_async_response(self) -> Optional[RAPDU]:
        return self.backend.last_async_response

    def send_raw_apdu(self, ins, p1=0x00, p2=0x00, data=b"") -> RAPDU:
        return self.backend.exchange(cla=CLA,
                                     ins=ins,
                                     p1=p1,
                                     p2=p2,
                                     data=data)
