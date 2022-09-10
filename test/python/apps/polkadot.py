from nacl.encoding import HexEncoder
from nacl.signing import VerifyKey,SigningKey
from nacl.exceptions import BadSignatureError
import traceback
from ragger.error import ExceptionRAPDU

ERR_SWAP_CHECK_WRONG_METHOD = ExceptionRAPDU(0x6985,b"Swap txn wrong method")
ERR_SWAP_CHECK_WRONG_METHOD_ARGS_CNT = ExceptionRAPDU(0x6985,b"Swap txn wrong method args count")
ERR_SWAP_CHECK_WRONG_DEST_ADDR = ExceptionRAPDU(0x6985,b"Swap txn wrong destination addr")
ERR_SWAP_CHECK_WRONG_AMOUNT = ExceptionRAPDU(0x6985,b"Swap txn wrong amount")
ERR_SWAP_CHECK_WRONG_REFUND_ADDRESS = ExceptionRAPDU(0x6a83,b"")

class Command:
    GET_VERSION = 0x00
    GET_ADDRESS = 0x01
    SIGN_TX = 0x02

class GetAddrP1:
    NO_CONFIRM = 0x00
    CONFIRM = 0x01

class SignP1:
    INIT = 0x00
    ADD = 0x01
    LAST = 0x02

class SignP2Last:
    ED25519 = 0x00
    SR25119 = 0x01

DOT_CONF = bytes([
    0x03, 0x44, 0x4F, 0x54, 0x08, 0x50, 0x6F, 0x6C, 0x6B, 0x61, 0x64, 0x6F, 
    0x74, 0x05, 0x03, 0x44, 0x4F, 0x54, 0x12
])

DOT_CONF_DER_SIGNATURE = bytes([
    0x30, 0x45, 0x02, 0x21, 0x00, 0xAE, 0x72, 0x48, 0x1D, 0x66, 0xC0, 0x41, 
    0xAD, 0x4F, 0xB3, 0xC4, 0x07, 0x69, 0x94, 0xFE, 0x62, 0x7C, 0x32, 0x81,
    0x50, 0x76, 0x34, 0x82, 0xD7, 0x3C, 0x03, 0x09, 0x10, 0xE3, 0x0C, 0xCB,
    0xFC, 0x02, 0x20, 0x74, 0x8A, 0xF3, 0x3B, 0xF1, 0x3B, 0x6D, 0xCA, 0x09,
    0xB2, 0x52, 0x90, 0xC8, 0x0C, 0xB5, 0xE4, 0x10, 0xD8, 0x4D, 0x53, 0x52,
    0x00, 0x13, 0xA5, 0xAF, 0x41, 0xB5, 0x49, 0x69, 0x6E, 0x4B, 0x47
])

# 1B (address kind) + 1B (length = 5) + 5*4B (path = 44'/60'/0'/0/0)
DOT_PACKED_DERIVATION_PATH = bytes([0x00,
                                    0x05,
                                    0x80, 0x00, 0x00, 0x2c,
                                    0x80, 0x00, 0x01, 0x62,
                                    0x80, 0x00, 0x00, 0x00,
                                    0x80, 0x00, 0x00, 0x00,
                                    0x80, 0x00, 0x00, 0x00])

DOT_PACKED_DERIVATION_PATH_SIGN_INIT = bytes([0x2c, 0x00, 0x00, 0x80,
                                         0x62, 0x01, 0x00, 0x80,
                                         0x00, 0x00, 0x00, 0x80,
                                         0x00, 0x00, 0x00, 0x80,
                                         0x00, 0x00, 0x00, 0x80])

class PolkadotClient:
    CLA = 0x90
    def __init__(self, client):
        self._client = client

    @property
    def client(self):
        return self._client

    def get_pubkey(self):
        msg = self.client.exchange(self.CLA, ins=Command.GET_ADDRESS, p1=0, p2=0, data=DOT_PACKED_DERIVATION_PATH_SIGN_INIT)
        return msg.data[:32].hex().encode()
    
    def sign_init(self):
        return self.client.exchange(self.CLA, ins=Command.SIGN_TX, p1=SignP1.INIT, data=DOT_PACKED_DERIVATION_PATH_SIGN_INIT)
        
    def sign_add(self,tx_chunk):
        return self.client.exchange(self.CLA, ins=Command.SIGN_TX, p1=SignP1.ADD,data=tx_chunk)
   
    def sign_last(self,tx_chunk):
        return self.client.exchange(self.CLA, ins=Command.SIGN_TX, p1=SignP1.LAST, p2=SignP2Last.ED25519, data=tx_chunk)
    
    def verify_signature(self,hex_key:bytes,signature:bytes,message:bytes) -> bool :
        # Create a VerifyKey object from a hex serialized public key
        verify_key = VerifyKey(hex_key, encoder=HexEncoder)
        # Check the validity of a message's signature
        try:
            verify_key.verify(message, signature, encoder=HexEncoder)
        except BadSignatureError:
            print("Wrong signature.")
            return False
        except Exception as e :
            print("Something went wrong.")
            print(e)
            print(traceback.format_exc())
            return False
        else:
            print("Signature is ok.")
            return True