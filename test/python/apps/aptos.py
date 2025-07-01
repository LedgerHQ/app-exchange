from enum import IntEnum
from ragger.utils import create_currency_config, RAPDU
from ragger.bip import pack_derivation_path
from typing import List, Optional

from aptos_sdk.transactions import RawTransaction, TransactionPayload, TransactionArgument, EntryFunction
from aptos_sdk.account import AccountAddress
from aptos_sdk.type_tag import StructTag, TypeTag
from aptos_sdk.bcs import Serializer


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

    def sign_tx(self, send_amount : int, fees : int, max_gas_amount : int , transmitter : str, destination : str) -> List[RAPDU]:
        sender = AccountAddress.from_str(transmitter)
        receiver =  AccountAddress.from_str(destination)

        # Transaction parameters
        sequence_number = 0
        expiration_timestamp = 0
        payload = EntryFunction.natural(
            "0x1::aptos_account",
            "transfer_coins",
            [TypeTag(StructTag.from_str("0x1::aptos_coin::AptosCoin"))],
            [
                TransactionArgument(receiver, Serializer.struct),
                TransactionArgument(send_amount, Serializer.u64),
            ],
        )

        # Create the raw transaction (TX_RAW)
        gas_unit_price = int(fees/max_gas_amount)
        txn = RawTransaction(
            sender=sender,
            sequence_number=sequence_number,
            payload=TransactionPayload(payload),
            max_gas_amount=max_gas_amount,
            gas_unit_price=gas_unit_price,
            expiration_timestamps_secs=expiration_timestamp,
            chain_id=1,
        )
        # Serialize the transaction
        serializer = Serializer()
        txn.serialize(serializer)
        transaction = serializer.output()
        # This is a salt required by the Nano App to make sure that the payload comes from Ledger Live host
        transaction = bytes.fromhex("b5e97db07fa0bd0e5598aa3643a9bc6f6693bddc1a9fec9e674a461eaa00b193" + transaction.hex())

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