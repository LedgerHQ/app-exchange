from typing import Optional
from dataclasses import dataclass

from ragger.utils import prefix_with_len

from .signing_authority import SigningAuthority, LEDGER_SIGNER

# Helper that can be called from outside if we want to generate signature errors easily
def sign_currency_conf(currency_conf: bytes, overload_signer: Optional[SigningAuthority]=None) -> bytes:
    if overload_signer is not None:
        signer = overload_signer
    else:
        signer = LEDGER_SIGNER

    return signer.sign(currency_conf)

# Currency configuration class, it contains coin metadata that will help the coin application
# display and check addresses for the related currency

@dataclass
class CurrencyConfiguration:
    # The ticker of this currency
    ticker: str
    # The CAL format configuration of this currency
    conf: bytes
    packed_derivation_path: bytes

    # Get the correct coin configuration, can specify a signer to use instead of the correct ledger test one
    def get_conf_for_ticker(self, overload_signer: Optional[SigningAuthority]=None) -> bytes:
        currency_conf = self.conf
        signed_conf = sign_currency_conf(currency_conf, overload_signer)
        derivation_path = self.packed_derivation_path
        return prefix_with_len(currency_conf) + signed_conf + prefix_with_len(derivation_path)