from .utils import LEDGER_TEST_PRIVATE_KEY_INT

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
