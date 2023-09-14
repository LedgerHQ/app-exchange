from typing import Optional

from ragger.utils import prefix_with_len

from .signing_authority import SigningAuthority, LEDGER_SIGNER

from .ethereum import ETH_PACKED_DERIVATION_PATH, ETH_CONF
from .ethereum_classic import ETC_PACKED_DERIVATION_PATH, ETC_CONF
from .litecoin import LTC_PACKED_DERIVATION_PATH, LTC_CONF
from .bitcoin import BTC_PACKED_DERIVATION_PATH, BTC_CONF
from .stellar import XLM_PACKED_DERIVATION_PATH, XLM_CONF
from .solana_utils import SOL_PACKED_DERIVATION_PATH, SOL_CONF
from .xrp import XRP_PACKED_DERIVATION_PATH, XRP_CONF
from .tezos_legacy import XTZ_PACKED_DERIVATION_PATH, XTZ_CONF
from .tezos_new import NTZ_PACKED_DERIVATION_PATH, NTZ_CONF
from .bsc import BSC_PACKED_DERIVATION_PATH, BSC_CONF

TICKER_ID_TO_CONF = {
    "ETC": ETC_CONF,
    "ETH": ETH_CONF,
    "BTC": BTC_CONF,
    "LTC": LTC_CONF,
    "XLM": XLM_CONF,
    "SOL": SOL_CONF,
    "XRP": XRP_CONF,
    "XTZ": XTZ_CONF,
    "NTZ": NTZ_CONF,
    "BSC": BSC_CONF,
}

TICKER_ID_TO_PACKED_DERIVATION_PATH = {
    "ETC": ETC_PACKED_DERIVATION_PATH,
    "ETH": ETH_PACKED_DERIVATION_PATH,
    "BTC": BTC_PACKED_DERIVATION_PATH,
    "LTC": LTC_PACKED_DERIVATION_PATH,
    "XLM": XLM_PACKED_DERIVATION_PATH,
    "SOL": SOL_PACKED_DERIVATION_PATH,
    "XRP": XRP_PACKED_DERIVATION_PATH,
    "XTZ": XTZ_PACKED_DERIVATION_PATH,
    "NTZ": NTZ_PACKED_DERIVATION_PATH,
    "BSC": BSC_PACKED_DERIVATION_PATH,
}

TICKER_ID_TO_PACKED_DERIVATION_PATH = {
    "ETC": ETC_PACKED_DERIVATION_PATH,
    "ETH": ETH_PACKED_DERIVATION_PATH,
    "BTC": BTC_PACKED_DERIVATION_PATH,
    "LTC": LTC_PACKED_DERIVATION_PATH,
    "XLM": XLM_PACKED_DERIVATION_PATH,
    "SOL": SOL_PACKED_DERIVATION_PATH,
    "XRP": XRP_PACKED_DERIVATION_PATH,
    "XTZ": XTZ_PACKED_DERIVATION_PATH,
    "NTZ": NTZ_PACKED_DERIVATION_PATH,
    "BSC": BSC_PACKED_DERIVATION_PATH,
}

# Helper that can be called from outside if we want to generate errors easily
def get_currency_conf(ticker_id: str) -> bytes:
    return TICKER_ID_TO_CONF[ticker_id]

# Helper that can be called from outside if we want to generate errors easily
def sign_currency_conf(currency_conf: bytes, overload_signer: Optional[SigningAuthority]=None) -> bytes:
    if overload_signer:
        signer = overload_signer
    else:
        signer = LEDGER_SIGNER

    return signer.sign(currency_conf)

# Helper that can be called from outside if we want to generate errors easily
def get_derivation_path(ticker_id: str) -> bytes:
    return TICKER_ID_TO_PACKED_DERIVATION_PATH[ticker_id]

# Get the correct coin configuration, can specify a signer to use instead of the correct ledger test one
def get_conf_for_ticker(ticker_id: str, overload_signer: Optional[SigningAuthority]=None) -> bytes:
    if ticker_id is None:
        return None
    currency_conf = get_currency_conf(ticker_id)
    signed_conf = sign_currency_conf(currency_conf, overload_signer)
    derivation_path = get_derivation_path(ticker_id)
    return prefix_with_len(currency_conf) + signed_conf + prefix_with_len(derivation_path)
