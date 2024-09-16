import traceback
from enum import IntEnum

from nacl.encoding import HexEncoder
from nacl.signing import VerifyKey,SigningKey
from nacl.exceptions import BadSignatureError

from ragger.utils import create_currency_config
from ragger.bip import bitcoin_pack_derivation_path, BtcDerivationPathFormat
from ragger.error import ExceptionRAPDU
from scalecodec.base import RuntimeConfiguration
from scalecodec.type_registry import load_type_registry_preset
from scalecodec.utils.ss58 import ss58_decode

class Method(IntEnum):
    BALANCE_TRANSFER_ALLOW_DEATH = 0x0500
    BALANCE_FORCE_TRANSFER = 0x0502

class AccountIdLookupType(IntEnum):
    ID = 0
    INDEX = 1
    RAW = 2
    ADDRESS32 = 3
    ADDRESS20 = 4

def _polkadot_address_to_pk(address: str) -> bytes:
    return bytes.fromhex(ss58_decode(address))

def _format_amount(amount: int) -> bytes:
    RuntimeConfiguration().update_type_registry(load_type_registry_preset("legacy"))
    obj = RuntimeConfiguration().create_scale_object('Compact<Balance>')
    scale_data = obj.encode(amount)
    return bytes(scale_data.get_remaining_bytes())

# Not sure what this exactly is but we don't actually care
UNKNOWN = bytes([0x85, 0x02, 0x00, 0x00])

SPEC_VERSION = 1001000
TX_VERSION = 25
CHECK_METADATA_HASH = 0x1

# We don't care about the block hash content
BLOCK_HASH = bytes([0x00] * 32)

GENESIS_HASH = bytes([
    0x91, 0xb1, 0x71, 0xbb, 0x15, 0x8e, 0x2d, 0x38, 0x48, 0xfa,
    0x23, 0xa9, 0xf1, 0xc2, 0x51, 0x82, 0xfb, 0x8e, 0x20, 0x31,
    0x3b, 0x2c, 0x1e, 0xb4, 0x92, 0x19, 0xda, 0x7a, 0x70, 0xce,
    0x90, 0xc3,
])

ERR_SWAP_CHECK_WRONG_METHOD = 0x6984
ERR_SWAP_CHECK_WRONG_METHOD_ARGS_CNT = 0x6984
ERR_SWAP_CHECK_WRONG_DEST_ADDR = 0x6984
ERR_SWAP_CHECK_WRONG_AMOUNT = 0x6984

class Command:
    GET_VERSION = 0x00
    GET_ADDRESS = 0x01
    SIGN_TX = 0x02

class GetAddrP1:
    NO_CONFIRM = 0x00
    CONFIRM = 0x01

class SignP1:
    INIT = 0x00
    ADD = 0x01
    LAST = 0x02

class SignP2Last:
    ED25519 = 0x00
    SR25119 = 0x01

DOT_CONF = create_currency_config("DOT", "Polkadot", ("DOT", 18))

DOT_PACKED_DERIVATION_PATH = bitcoin_pack_derivation_path(BtcDerivationPathFormat.LEGACY, "m/44'/354'/0'/0'/0'")

DOT_PACKED_DERIVATION_PATH_SIGN_INIT = bytes([0x2c, 0x00, 0x00, 0x80,
                                              0x62, 0x01, 0x00, 0x80,
                                              0x00, 0x00, 0x00, 0x80,
                                              0x00, 0x00, 0x00, 0x80,
                                              0x00, 0x00, 0x00, 0x80])

MAX_CHUNK_SIZE = 250


class PolkadotClient:
    CLA = 0xF9
    def __init__(self, client):
        self._client = client

    @property
    def client(self):
        return self._client

    def get_pubkey(self):
        data = DOT_PACKED_DERIVATION_PATH_SIGN_INIT + bytes([0x00, 0x00])
        msg = self.client.exchange(self.CLA, ins=Command.GET_ADDRESS, p1=0, p2=0, data=data)
        return msg.data[:32].hex().encode()

    def sign_init(self):
        data = DOT_PACKED_DERIVATION_PATH_SIGN_INIT + bytes([0x00, 0x00])
        return self.client.exchange(self.CLA, ins=Command.SIGN_TX, p1=SignP1.INIT, p2=SignP2Last.ED25519, data=data)

    def sign_last(self, message):
        # return self.client.exchange(self.CLA, ins=Command.SIGN_TX, p1=SignP1.LAST, p2=SignP2Last.ED25519, data=tx_chunk)
        message_splited = [message[x:x + MAX_CHUNK_SIZE] for x in range(0, len(message), MAX_CHUNK_SIZE)]
        for index, chunk in enumerate(message_splited):
            payload_type = SignP1.ADD
            if index == len(message_splited) - 1:
                payload_type = SignP1.LAST

            response=self.client.exchange(self.CLA, ins=Command.SIGN_TX, p1=payload_type, p2=SignP2Last.ED25519, data=chunk)

        # Send message to be signed
        return response

    def verify_signature(self, hex_key:bytes, signature:bytes, message:bytes) -> bool :
        # Create a VerifyKey object from a hex serialized public key
        verify_key = VerifyKey(hex_key, encoder=HexEncoder)
        # Check the validity of a message's signature
        try:
            verify_key.verify(message, signature, encoder=HexEncoder)
        except BadSignatureError:
            print("Wrong signature.")
            return False
        except Exception as e :
            print("Something went wrong.")
            print(e)
            print(traceback.format_exc())
            return False
        else:
            print("Signature is ok.")
            return True

    def craft_valid_polkadot_transaction(address, send_amount, fees, memo) -> bytes:
        callData = bytes.fromhex("050004f54219c421622fc214fcfc8b7674ff7ca4fe90e73344160e9b8964faf26d422151bc43e97e")
        seIncludedInExtrinsic = bytes.fromhex("692203513a618d3339eae83b48e03e0cb587b4eb1dcccb5b01")
        seIncludedInSignedData = bytes.fromhex("164a0f001a00000091b171bb158e2d3848fa23a9f1c25182fb8e20313b2c1eb49219da7a70ce90c351d148bb45daee053826ad0eb7b83dbc47a6dcd861fed70ca99ec6ba97d10fa601f19b9871efd816a3912a6eb8a021214f55ab3d5519bf7544271e12098c971d3f")
        signedExtensions = seIncludedInExtrinsic + seIncludedInSignedData
        blob = callData + signedExtensions
        # blob = bytes.fromhex("050000bb03b7e8d310683e01629eab503bff3a75cd912e6ba66e8b12957f07c50b480e33140d67721d1888aec69ba70e0cb5245e00be8bb6e233a22198dc3f087235eadab140bf59048a01164a0f001a00000091b171bb158e2d3848fa23a9f1c25182fb8e20313b2c1eb49219da7a70ce90c391b171bb158e2d3848fa23a9f1c25182fb8e20313b2c1eb49219da7a70ce90c301f19b9871efd816a3912a6eb8a021214f55ab3d5519bf7544271e12098c971d3f")
        return blob
        # metadata = bytes.fromhex("6c000341000000030502082873705f72756e74696d65384d756c74695369676e6174757265011c45643235353139040016a1010148656432353531393a3a5369676e617475726500cd02082873705f72756e74696d65384d756c74695369676e6174757265011c53723235353139040016d1020148737232353531393a3a5369676e617475726504cd02082873705f72756e74696d65384d756c74695369676e617475726501144563647361040016d502014065636473613a3a5369676e617475726508cd020c1c73705f636f72651c73723235353139245369676e617475726500040016a50101205b75383b2036345dd1020c1c73705f636f7265146563647361245369676e6174757265000400160502017c5b75383b205349474e41545552455f53455249414c495a45445f53495a455dd50210306672616d655f73797374656d28657874656e73696f6e733c636865636b5f6d6f7274616c69747938436865636b4d6f7274616c697479000400169506010c4572619106102873705f72756e74696d651c67656e657269630c6572610c45726101244d6f7274616c31303504000300a501950610306672616d655f73797374656d28657874656e73696f6e732c636865636b5f6e6f6e636528436865636b4e6f6e6365000400110120543a3a4e6f6e63659906086870616c6c65745f7472616e73616374696f6e5f7061796d656e74604368617267655472616e73616374696f6e5061796d656e7400040013013042616c616e63654f663c543e9d0608746672616d655f6d657461646174615f686173685f657874656e73696f6e44436865636b4d6574616461746148617368000401106d6f646516a50601104d6f6465a10608746672616d655f6d657461646174615f686173685f657874656e73696f6e104d6f6465011c456e61626c65640004a5060c1c73705f636f72651863727970746f2c4163636f756e7449643332000400160401205b75383b2033325d000003200000000304083c7072696d69746976655f74797065731048323536000400160401205b75383b2033325d0c0002031004184f7074696f6e0110536f6d650400160400042800031400000003600840706f6c6b61646f745f72756e74696d652c52756e74696d6543616c6c012042616c616e636573040016210101b50173656c663a3a73705f6170695f68696464656e5f696e636c756465735f636f6e7374727563745f72756e74696d653a3a68696464656e5f696e636c7564653a3a64697370617463680a3a3a43616c6c61626c6543616c6c466f723c42616c616e6365732c2052756e74696d653e14cc0c2873705f72756e74696d65306d756c746961646472657373304d756c746941646472657373010849640400160001244163636f756e744964001d010c2873705f72756e74696d65306d756c746961646472657373304d756c7469416464726573730114496e64657804001501304163636f756e74496e646578041d010c2873705f72756e74696d65306d756c746961646472657373304d756c746941646472657373010c52617704001610011c5665633c75383e081d010c2873705f72756e74696d65306d756c746961646472657373304d756c74694164647265737301244164647265737333320400160401205b75383b2033325d0c1d010c2873705f72756e74696d65306d756c746961646472657373304d756c74694164647265737301244164647265737332300400166001205b75383b2032305d101d010c3c70616c6c65745f62616c616e6365731870616c6c65741043616c6c01507472616e736665725f616c6c6f775f646561746808011064657374161d0101504163636f756e7449644c6f6f6b75704f663c543e011476616c7565130128543a3a42616c616e63650021010c1c73705f636f72651c65643235353139245369676e617475726500040016a50101205b75383b2036345da10100034000000003a5016c27080000a8080000a9080000aa080000ab080000ac080000e50b00004f0c0000e60c0000e70c0000e80c0000ea0c00007506000076060000780600007906000084060000b30600002107000078070000790700007a0700007b0700007c0700007d070000d1070000d20700000d01d91faeff13ea34cd1289e65c73516e265a5ef5f957b33f85a78a53123a67d5f9c98c6854e15285c36114e1dbb18eb1afd27ef0a07f0b068ddded3de8a0a1aa807e6aa2ebf86a4faade7b5bad4d15c56f80caa5ecaac247f46779b515de2414f61fac61ebba48d8659bffffc08b6d188b86d2ac7d36873c7fcdf99028fdedb70fbb54bb1d5b1cf889275efd936a4b05571c0552ee6b2719843fbbd92af062b90fd020b78a85ef07211ec7d3e1d0fd4b412f281d78dcc71634ea3b449701e161ce22c9a759ee1628b3e9a29fa5f8c433e4f9bc51e4c30d4ccdf9eda7f95d07280f8c8456bf1f359f5d3c076575c75d6283503da3bbc42b45e526afad1aff4ebedef361e54470ba49e7a8eab5e179a1ef262ce94dd611a8fca4e27c52fed9808384596424dfaff8f8666f8d3a7a76f9ac7610bffeb256921719848bbe34ada42e3e499aa1a05cc8e7944784eed134cfea025ed2d2c9fd463f7bdea377f9856508f061432c8cfd0ab976f5f7aaf4976f2ebd222093224863bc1131fe367016b1a583669d41ff5571cc4c8dab7a03af9314e9e0498d00063fb0f54535447537660519397da7e7c071cfbaa2fc4133391869970de71a455c83718e52b47fd801f058f4147c6d7f2349d2171ddc47b9d1d9a0007d35736d79a31c950b19216e8a444df4221431cb1955b43a56b26c80c738f0620d3a0072f2e4cd62043c411fa72b551ba558f4beea9edb9c2bbaa6c2bbd9aeab83d9047a89f2d664fc04fde2c2f430441558d114e34c8b589c3e7bde066c8c56b91aba3156bb5905a9248599307c7017a323594e537bb228a39b9de0df4ca0facb90cf7ea8bbfd0ff82a3339d51c2f23d2547ef9e2560b0584ecfc68224593da35fbc5e1916c9b3051c32ff21738da88b945636026026769703890f2bfcd91c0a8485055b023130eb856e4dd5c5bc2795c2d74ccab62e40896ee49efa1f32274871fb4796b5e61267b392d4db9993b84485d4761193309f7b6bdc4c3b10e8509837a29b5889a3fe637ecf774f6f57e89499ea74327aea63191afc978e3615bd5f3a72d2878c6b35aec2342f94d4ea473084b320bab476103eeca62ea9f79229451cf1e5d9eb678f62a67f38e9a92fe1f6acedc36fc32454f8929ef4b3f27ffe3a2312791885b507618fc7c1fe984361272beb8bebb43e5aa5a2596340859fd6f047693bfb9ec262ab3f6d5e20d16e3e662d7e897bd888235365db31818ea06de59c346059f205bfc79561b4fc0c6247752f570f0d3bfb03a6cdb7b2edaadd8fba7473c96648ae89e76f3073b8d9fe76ea12e2cbecd7d91c3cae11497f8135206b750f8e7bc9f338572945a63b252eb7ffe20b6f71c69b1cdeb0aaadf452dffcc3353d4eff613696d2792df127669d9bdbd40823c07596bdd1e495935bb6c1eef7d892072e08b4187f8d1d9628f130c25a33a67b8ee375917a7bfef6833130aeda694a5aca794c831a87f505c2a0502050e1c48bef1f0729d80b4065cdba938ef9dccb765324d97bce19d988731b3c5284d3a67726bc13436ce5a28aa2f6df53e7fcc322e9de5e7a57c48f1e0fa1278d344497dfba612626dde397df6083b375abdbe4b54a7ca04038f8ecb1cfa2b8001d3814e151905ab6499c76ccb290d3cc9fa2f41bd00139140b7206e31ff9d98e4beef1d1a2e20bbc4a225773b9327590503729e589420b1a75d86eaabff22d7ceb0a3bce7985ac4ce86e36c57c1716dc9c7e103b2ad5a424a8d0e86dfa17f9a07c02b324d207aa7db57748e03582b2b14252098b18ff936647f35737cb48bf547b6ff20823184c6209dc2adace5018e8a711801511ca777e64cd925444219cf37d40c56c433f7d63769f9582530589a8e112a54127b269dd26c16d6665c9389b8dc10d88d42dbb05c9df62fd4d4f1ef3ed48d8f218ba84323b17ecdbb01c86b3d7ba8daae57d0da83717bb70f9cec739c5b1e1370a406db4c34d0f424befccfec9860dc716868c6c9d6c7fb900bae783b379a0037aca2d77760a9e01219f4899a0f42e0c50e0d67e31a30dc25d318a04a22cf00bb65e1f0a2e8432c9ca90933b69d043c5fb4b7ed952375643ae4889918cd3d29eeedc5ff001d42425a308034140e027d4b18944239aa7dbdcf64e6faf2a3d452982ba24b28c7f3fc7de9f99e7b6603d7f1e1e2c03f9ad10ffab2f383b74c33ba8b1cfbe5b7edd24f6fa776ccf0a37a1d87bcacbcd6e5752149faa4da3f2667208e7c70a08d6aa20911aab00a4cacc0f058acae0c9836d7106ce586976341ec3b5d9625a783952b2463c049f0707fc0e6a5cf8884cce54bbc9b654aad1781439db1581d0a4edb60822049d23fe5f456a4b0071b9d82e21b3fecf7acf7a2e5d7486daeeb7ef5aacbc2a2913312c05b5f02722591686609fac1829387906fba98c4e7f8275de5254a83927875402678c34c67acb5bc0a209b55768e68a5b106566467569f7de5ff8403fe5074b88889a9850cd3c8fcf1a7f4546358e40ff4f29373a776f97c216e6b232a2280b144a0ca1a82f16119266f8d3acd56c738c2298edd999f6b810e74c286cdea2f5af88a75145707c161d9e7abad3aff1bd2b3b24302941960ae2647dd03562878ec82c46a94845231550df4cc68fc90dea150d869ec1fa070ae61dd16fec38e66014bc7f7cb14c4f1a75923f35f284467727486a7b4d5c70f467d57426d4f3d703e5b451aa9777b003f394871e76f320b87267ce254816d9dd82c2ce527c54c21a3ccceaec19d9bfe8b8d52c4408d174ba6a56144fc63f8147feb7c502454929f57771c41c4d35b5cbdc2b3e9881e3078dddd5e7002f6339f94892d6bfe70f84bc3757b1147ec68adb8a244e0d073a318c3099088de29e3a58df10188278d32ff91f814fffa2df6718b2bad4c6a62589035e35a2cfd5312ab19494be63b92f8db57c54b572b22bc69e54966e533d3a9e241bc3fe7aef39758201e94d35efe7ba8a11f6f4ee3dc6b1d0e4fc2aa23f33c08d5916e5440797986cde5bc83e08693709c1404161d0116cc16cd022848436865636b4e6f6e5a65726f53656e646572151540436865636b5370656356657273696f6e150538436865636b547856657273696f6e150530436865636b47656e6573697315160c38436865636b4d6f7274616c697479169106160c28436865636b4e6f6e6365169906152c436865636b5765696768741515604368617267655472616e73616374696f6e5061796d656e74169d06154850726576616c696461746541747465737473151544436865636b4d657461646174614861736816a1061628164a0f0020706f6c6b61646f7400000a0c444f54")
        # tx_blob = blob + shortened_metadata
        # tx_blob = blob + metadata
        # return Method.BALANCE_TRANSFER_ALLOW_DEATH.to_bytes(2, "big") \
        #        + AccountIdLookupType.ID.to_bytes(1, "big") \
        #        + _polkadot_address_to_pk(address) \
        #        + _format_amount(send_amount) \
        #        + UNKNOWN \
        #        + CHECK_METADATA_HASH.to_bytes(1, "little") \
        #        + SPEC_VERSION.to_bytes(4, "little") \
        #        + TX_VERSION.to_bytes(4, "little") \
        #        + GENESIS_HASH \
        #        + BLOCK_HASH \
        #        + bytes(0x01) + bytes([0x00] * 32)
        # return tx_blob

    def craft_invalid_polkadot_transaction(address, send_amount, fees, memo) -> bytes:
        force_transfer = Method.BALANCE_FORCE_TRANSFER.to_bytes(2, "big") \
                       + bytes([0x00, 0xdc, 0x5a, 0xda, 0x10, 0xee, 0xdd, 0x89, 0x81, 0x92,
                                0x78, 0xb0, 0x92, 0x35, 0x87, 0x80, 0x3d, 0x7d, 0xb2, 0x07,
                                0xe1, 0xdc, 0x7e, 0x1c, 0x18, 0x42, 0x4f, 0xa4, 0xad, 0x59,
                                0xb4, 0x00, 0x19, 0x00, 0xb0, 0x0b, 0x9f, 0x27, 0xc2, 0xd1,
                                0xd2, 0x16, 0x01, 0x58, 0x51, 0xdc, 0x3a, 0x69, 0xc8, 0xab,
                                0x52, 0xb2, 0x86, 0x62, 0xe7, 0xfa, 0x31, 0x7c, 0x07, 0xad,
                                0x1f, 0x34, 0xa4, 0xdf, 0xcd, 0x62, 0x07, 0x70, 0xf9, 0xdb,
                                0xdf, 0x02, 0x55, 0x02, 0x00, 0x00])

        return force_transfer \
               + SPEC_VERSION.to_bytes(4, "little") \
               + TX_VERSION.to_bytes(4, "little") \
               + GENESIS_HASH \
               + BLOCK_HASH

#050004f54219c421622fc214fcfc8b7674ff7ca4fe90e73344160e9b8964faf26d422151bc43e97e692203513a618d3339eae83b48e03e0cb587b4eb1dcccb5b
# Tip
# CheckMetadataHash 01
# CheckSpecVersion  164a0f00
# CheckTxVersion    1a000000
# CheckGenesis      91b171bb158e2d3848fa23a9f1c25182fb8e20313b2c1eb49219da7a70ce90c3
# Mortality         51d148bb45daee053826ad0eb7b83dbc47a6dcd861fed70ca99ec6ba97d10fa6
# CheckMetadataHash 01f19b9871efd816a3912a6eb8a021214f55ab3d5519bf7544271e12098c971d3f
