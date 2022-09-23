from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec, dh
from cryptography.hazmat.primitives import serialization, hashes


# A helper class to simulate an Exchange partner
class ExchangePartnerIdentity:
    _private_key: ec.EllipticCurvePrivateKey
    _public_key: dh.DHPublicKey
    _name: str
    _credentials: bytes

    def __init__(self, curve: ec.EllipticCurve, name: str):
        """
        Initializes the partner data

        :param curve: The EllipticCurve to use for the key generation
        :type curve: ec.EllipticCurve
        :param name: The partner name to include in the credentials
        :type name: str
        """

        # Set self identity
        self._private_key = ec.generate_private_key(curve, backend=default_backend())
        self._public_key = self._private_key.public_key()
        self._name = name

        # Generate credentials from self identity
        encoded_name = self._name.encode('utf-8')
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        self._credentials = len(encoded_name).to_bytes(1, "big") + encoded_name + public_bytes

    @property
    def credentials(self) -> bytes:
        """
        :return: The partner credentials correctly formated.
        :rtype: bytes
        """
        return self._credentials

    def sign(self, payload_to_sign: bytes) -> bytes:
        """
        Sign the requested data

        :param payload_to_sign: The payload the parnter needs to sign
        :type payload_to_sign: bytes

        :return: The payload signed
        :rtype: bytes
        """
        return self._private_key.sign(payload_to_sign, ec.ECDSA(hashes.SHA256()))

