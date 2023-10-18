from typing import Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec, dh
from cryptography.hazmat.primitives import serialization, hashes

from ragger.utils import prefix_with_len


# A helper class to simulate a Signing Authority
class SigningAuthority:
    _private_key: ec.EllipticCurvePrivateKey
    _public_key: dh.DHPublicKey
    _name: str
    _credentials: bytes
    _credentials_ng: bytes

    def __init__(self, curve: ec.EllipticCurve, name: str, existing_key: Optional[int] = None):
        """
        Initializes the partner data

        :param curve: The EllipticCurve to use for the key generation
        :type curve: ec.EllipticCurve
        :param name: The partner name to include in the credentials
        :type name: str
        :param name: Specify if the signer should use the test key as private key or a randomly generated key
        :type name: Optional[int]
        """

        # Set self identity
        if existing_key != None:
            self._private_key = ec.derive_private_key(private_value=existing_key,
                                                      curve=curve,
                                                      backend=default_backend())
        else:
            self._private_key = ec.generate_private_key(curve=curve, backend=default_backend())
        self._public_key = self._private_key.public_key()
        self._name = name

        # Generate credentials from self identity
        prefixed_encoded_name = prefix_with_len(self._name.encode())
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        self._credentials = prefixed_encoded_name + public_bytes

        if isinstance(curve, ec.SECP256K1):
            curve_id = int.to_bytes(0x00, length=1, byteorder='big')
        elif isinstance(curve, ec.SECP256R1):
            curve_id = int.to_bytes(0x01, length=1, byteorder='big')
        else:
            raise ValueError
        self._credentials_ng = prefixed_encoded_name + curve_id + public_bytes

    @property
    def credentials(self) -> bytes:
        """
        :return: The partner credentials correctly formatted for legacy flows
        :rtype: bytes
        """
        return self._credentials

    @property
    def credentials_ng(self) -> bytes:
        """
        :return: The partner credentials correctly formatted for ng flows
        :rtype: bytes
        """
        return self._credentials_ng

    def sign(self, payload_to_sign: bytes) -> bytes:
        """
        Sign the requested data

        :param payload_to_sign: The payload the partner needs to sign
        :type payload_to_sign: bytes

        :return: The payload signed
        :rtype: bytes
        """
        return self._private_key.sign(payload_to_sign, ec.ECDSA(hashes.SHA256()))

# The fake Ledger private key recognized by exchange app compiled with the test flag
# No usage outside of testing
LEDGER_TEST_PRIVATE_KEY_HEX = "b1ed47ef58f782e2bc4d5abe70ef66d9009c2957967017054470e0f3e10f5833"
LEDGER_TEST_PRIVATE_KEY_INT = int(LEDGER_TEST_PRIVATE_KEY_HEX, 16)
LEDGER_SIGNER = SigningAuthority(curve=ec.SECP256K1(), name="ledger_test_signer", existing_key=LEDGER_TEST_PRIVATE_KEY_INT)
