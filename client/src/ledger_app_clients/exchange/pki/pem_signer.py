import importlib.resources

import os
import hashlib
from ecdsa import SigningKey
from ecdsa.util import sigencode_der


class KeySigner:
    def __init__(self, pem_name: str):
        """
        Initialize the KeySigner instance with a specific PEM file.

        :param pem_name: Name of the PEM file (e.g., 'trusted_name.pem')
        """
        try:
            with importlib.resources.open_text("ledger_app_clients.exchange.pki", pem_name) as pem_file:
                self._signing_key = SigningKey.from_pem(pem_file.read(), hashlib.sha256)
        except FileNotFoundError:
            raise FileNotFoundError(f"PEM file not found in package: {pem_name}")

    def sign_data(self, data: bytes) -> bytes:
        """
        Generate a SECP256K1 signature of the given data.

        :param data: Data to sign as bytes.
        :return: Signature as bytes in DER format.
        """
        return self._signing_key.sign_deterministic(data, sigencode=sigencode_der)
