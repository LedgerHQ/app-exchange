from ragger.utils import create_currency_config
from ragger.bip import BtcDerivationPathFormat, bitcoin_pack_derivation_path

BTC_CONF = create_currency_config("BTC", "Bitcoin")

BTC_PACKED_DERIVATION_PATH = bitcoin_pack_derivation_path(BtcDerivationPathFormat.BECH32, "m/44'/0'/0'/0/0")
