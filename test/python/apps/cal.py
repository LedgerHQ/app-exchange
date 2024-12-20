from typing import Optional
from dataclasses import dataclass

from ragger.utils import prefix_with_len

from .signing_authority import SigningAuthority, LEDGER_SIGNER

# Eth family
from .ethereum import ETH_PACKED_DERIVATION_PATH, ETH_CONF
from .ethereum import ETC_PACKED_DERIVATION_PATH, ETC_CONF
from .ethereum import BSC_PACKED_DERIVATION_PATH, BSC_CONF, BSC_CONF_LEGACY
from .ethereum import DAI_PACKED_DERIVATION_PATH, DAI_CONF

from .litecoin import LTC_PACKED_DERIVATION_PATH, LTC_CONF
from .bitcoin import BTC_PACKED_DERIVATION_PATH, BTC_CONF
from .stellar import XLM_PACKED_DERIVATION_PATH, XLM_CONF
from .solana_utils import SOL_PACKED_DERIVATION_PATH, SOL_CONF
from .solana_utils import JUP_PACKED_DERIVATION_PATH, JUP_CONF
from .solana_utils import SOL_USDC_PACKED_DERIVATION_PATH, SOL_USDC_CONF
from .xrp import XRP_PACKED_DERIVATION_PATH, XRP_CONF
from .tezos import XTZ_PACKED_DERIVATION_PATH, XTZ_CONF
from .polkadot import DOT_PACKED_DERIVATION_PATH, DOT_CONF
from .ton import TON_PACKED_DERIVATION_PATH, TON_CONF
from .tron import TRX_PACKED_DERIVATION_PATH, TRX_CONF
from .tron import TRX_USDT_CONF, TRX_USDC_CONF, TRX_TUSD_CONF, TRX_USDD_CONF
from .cosmos import COSMOS_PACKED_DERIVATION_PATH, COSMOS_CONF
from .cardano import ADA_BYRON_PACKED_DERIVATION_PATH, ADA_SHELLEY_PACKED_DERIVATION_PATH, ADA_CONF
from .near import NEAR_PACKED_DERIVATION_PATH, NEAR_CONF

@dataclass
class CurrencyConfiguration:
    ticker: str
    conf: bytes
    packed_derivation_path: bytes

    # Get the correct coin configuration, can specify a signer to use instead of the correct ledger test one
    def get_conf_for_ticker(self, overload_signer: Optional[SigningAuthority]=None) -> bytes:
        currency_conf = self.conf
        signed_conf = sign_currency_conf(currency_conf, overload_signer)
        derivation_path = self.packed_derivation_path
        return prefix_with_len(currency_conf) + signed_conf + prefix_with_len(derivation_path)

ETC_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="ETC", conf=ETC_CONF, packed_derivation_path=ETC_PACKED_DERIVATION_PATH)
ETH_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="ETH", conf=ETH_CONF, packed_derivation_path=ETH_PACKED_DERIVATION_PATH)
BTC_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="BTC", conf=BTC_CONF, packed_derivation_path=BTC_PACKED_DERIVATION_PATH)
LTC_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="LTC", conf=LTC_CONF, packed_derivation_path=LTC_PACKED_DERIVATION_PATH)
XLM_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="XLM", conf=XLM_CONF, packed_derivation_path=XLM_PACKED_DERIVATION_PATH)
SOL_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="SOL", conf=SOL_CONF, packed_derivation_path=SOL_PACKED_DERIVATION_PATH)
JUP_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="JUP", conf=JUP_CONF, packed_derivation_path=JUP_PACKED_DERIVATION_PATH)
SOL_USDC_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="USDC", conf=SOL_USDC_CONF, packed_derivation_path=SOL_USDC_PACKED_DERIVATION_PATH)
XRP_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="XRP", conf=XRP_CONF, packed_derivation_path=XRP_PACKED_DERIVATION_PATH)
XTZ_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="XTZ", conf=XTZ_CONF, packed_derivation_path=XTZ_PACKED_DERIVATION_PATH)
BNB_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="BNB", conf=BSC_CONF, packed_derivation_path=BSC_PACKED_DERIVATION_PATH)
BNB_LEGACY_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="BNB", conf=BSC_CONF_LEGACY, packed_derivation_path=BSC_PACKED_DERIVATION_PATH)
DAI_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="DAI", conf=DAI_CONF, packed_derivation_path=DAI_PACKED_DERIVATION_PATH)
DOT_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="DOT", conf=DOT_CONF, packed_derivation_path=DOT_PACKED_DERIVATION_PATH)
TON_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="TON", conf=TON_CONF, packed_derivation_path=TON_PACKED_DERIVATION_PATH)
TON_USDT_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="TON", conf=TON_CONF, packed_derivation_path=TON_PACKED_DERIVATION_PATH)
TRX_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="TRX", conf=TRX_CONF, packed_derivation_path=TRX_PACKED_DERIVATION_PATH)
USDT_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="USDT", conf=TRX_USDT_CONF, packed_derivation_path=TRX_PACKED_DERIVATION_PATH)
USDC_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="USDC", conf=TRX_USDC_CONF, packed_derivation_path=TRX_PACKED_DERIVATION_PATH)
TUSD_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="TUSD", conf=TRX_TUSD_CONF, packed_derivation_path=TRX_PACKED_DERIVATION_PATH)
USDD_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="USDD", conf=TRX_USDD_CONF, packed_derivation_path=TRX_PACKED_DERIVATION_PATH)
COSMOS_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="ATOM", conf=COSMOS_CONF, packed_derivation_path=COSMOS_PACKED_DERIVATION_PATH)
ADA_BYRON_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="ADA", conf=ADA_CONF, packed_derivation_path=ADA_BYRON_PACKED_DERIVATION_PATH)
ADA_SHELLEY_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="ADA", conf=ADA_CONF, packed_derivation_path=ADA_SHELLEY_PACKED_DERIVATION_PATH)
NEAR_CURRENCY_CONFIGURATION = CurrencyConfiguration(ticker="NEAR", conf=NEAR_CONF, packed_derivation_path=NEAR_PACKED_DERIVATION_PATH)

# Helper that can be called from outside if we want to generate errors easily
def sign_currency_conf(currency_conf: bytes, overload_signer: Optional[SigningAuthority]=None) -> bytes:
    if overload_signer is not None:
        signer = overload_signer
    else:
        signer = LEDGER_SIGNER

    return signer.sign(currency_conf)


