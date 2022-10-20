from ..utils import BtcDerivationPathFormat, bitcoin_pack_derivation_path, create_currency_config

BTC_CONF = create_currency_config("BTC", "Bitcoin")

BTC_PACKED_DERIVATION_PATH = bitcoin_pack_derivation_path(BtcDerivationPathFormat.BECH32, "m/44'/0'/0'/0/0")
