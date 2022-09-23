from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes


# The fake Ledger private key recognized by apps compiled with the test flag
# No usage outside of testing
LEDGER_TEST_PRIVATE_KEY_HEX = "b1ed47ef58f782e2bc4d5abe70ef66d9009c2957967017054470e0f3e10f5833"
LEDGER_TEST_PRIVATE_KEY_BYTES = bytes.fromhex(LEDGER_TEST_PRIVATE_KEY_HEX)
LEDGER_TEST_PRIVATE_KEY_INT = int(LEDGER_TEST_PRIVATE_KEY_HEX, 16)


# A helper class to simulate Ledger signed data
# It uses the Ledger testing key by default, or a randomly generated key if specified at init
class LedgerTestSigner:
    _private_key: ec.EllipticCurvePrivateKey

    def __init__(self, use_test_key: bool = True):
        """
        Initializes the Ledger test signer

        :param use_test_key: specify if the signer should use the test key as private key or a randomly generated key
        :type use_test_key: bool
        """
        if use_test_key:
            device_number = LEDGER_TEST_PRIVATE_KEY_INT
            self._private_key = ec.derive_private_key(private_value=device_number,
                                                     curve=ec.SECP256K1(),
                                                     backend=default_backend())
        else:
            self._private_key = ec.generate_private_key(curve=ec.SECP256K1(), backend=default_backend())

    def sign(self, payload_to_sign: bytes) -> bytes:
        """
        Sign the requested data

        :param payload_to_sign: The payload the parnter needs to sign
        :type payload_to_sign: bytes

        :return: The payload signed
        :rtype: bytes
        """
        return self._private_key.sign(payload_to_sign, ec.ECDSA(hashes.SHA256()))
