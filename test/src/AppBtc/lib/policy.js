"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DefaultWalletPolicy = exports.WalletPolicy = void 0;
const bitcoinjs_lib_1 = require("bitcoinjs-lib");
const buffertools_1 = require("./buffertools");
const merkle_1 = require("./merkle");
/**
 * The Bitcon hardware app uses a descriptors-like thing to describe
 * how to construct output scripts from keys. A "Wallet Policy" consists
 * of a "Descriptor Template" and a list of "keys". A key is basically
 * a serialized BIP32 extended public key with some added derivation path
 * information. This is documented at
 * https://github.com/LedgerHQ/app-bitcoin-new/blob/master/doc/wallet.md
 */
class WalletPolicy {
    constructor(name, descriptorTemplate, keys) {
        this.name = name;
        this.descriptorTemplate = descriptorTemplate;
        this.keys = keys;
    }
    getWalletId() {
        // wallet_id (sha256 of the wallet serialization),
        return bitcoinjs_lib_1.crypto.sha256(this.serialize());
    }
    serialize() {
        const keyBuffers = this.keys.map((k) => {
            return Buffer.from(k, 'ascii');
        });
        const m = new merkle_1.Merkle(keyBuffers.map((k) => (0, merkle_1.hashLeaf)(k)));
        const buf = new buffertools_1.BufferWriter();
        buf.writeUInt8(0x01); // wallet type (policy map)
        buf.writeVarSlice(Buffer.from(this.name, 'ascii'));
        buf.writeVarSlice(Buffer.from(this.descriptorTemplate, 'ascii'));
        buf.writeVarInt(this.keys.length);
        buf.writeSlice(m.getRoot());
        return buf.buffer();
    }
}
exports.WalletPolicy = WalletPolicy;
/**
 * The Bitcon hardware app uses a descriptors-like thing to describe
 * how to construct output scripts from keys. A "Wallet Policy" consists
 * of a "Descriptor Template" and a list of "keys". A key is basically
 * a serialized BIP32 extended public key with some added derivation path
 * information. This is documented at
 * https://github.com/LedgerHQ/app-bitcoin-new/blob/master/doc/wallet.md
 */
class DefaultWalletPolicy extends WalletPolicy {
    constructor(descriptorTemplate, key) {
        super('', descriptorTemplate, [key]);
    }
}
exports.DefaultWalletPolicy = DefaultWalletPolicy;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicG9saWN5LmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9wb2xpY3kudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBQUEsaURBQXVDO0FBRXZDLCtDQUE2QztBQUM3QyxxQ0FBNEM7QUFFNUM7Ozs7Ozs7R0FPRztBQUNILE1BQWEsWUFBWTtJQUl2QixZQUNFLElBQVksRUFDWixrQkFBMEIsRUFDMUIsSUFBdUI7UUFFdkIsSUFBSSxDQUFDLElBQUksR0FBRyxJQUFJLENBQUM7UUFDakIsSUFBSSxDQUFDLGtCQUFrQixHQUFHLGtCQUFrQixDQUFDO1FBQzdDLElBQUksQ0FBQyxJQUFJLEdBQUcsSUFBSSxDQUFDO0lBQ25CLENBQUM7SUFFRCxXQUFXO1FBQ1Qsa0RBQWtEO1FBQ2xELE9BQU8sc0JBQU0sQ0FBQyxNQUFNLENBQUMsSUFBSSxDQUFDLFNBQVMsRUFBRSxDQUFDLENBQUM7SUFDekMsQ0FBQztJQUVELFNBQVM7UUFDUCxNQUFNLFVBQVUsR0FBRyxJQUFJLENBQUMsSUFBSSxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUMsRUFBRSxFQUFFO1lBQ3JDLE9BQU8sTUFBTSxDQUFDLElBQUksQ0FBQyxDQUFDLEVBQUUsT0FBTyxDQUFDLENBQUM7UUFDakMsQ0FBQyxDQUFDLENBQUM7UUFDSCxNQUFNLENBQUMsR0FBRyxJQUFJLGVBQU0sQ0FBQyxVQUFVLENBQUMsR0FBRyxDQUFDLENBQUMsQ0FBQyxFQUFFLEVBQUUsQ0FBQyxJQUFBLGlCQUFRLEVBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO1FBRXpELE1BQU0sR0FBRyxHQUFHLElBQUksMEJBQVksRUFBRSxDQUFDO1FBQy9CLEdBQUcsQ0FBQyxVQUFVLENBQUMsSUFBSSxDQUFDLENBQUMsQ0FBQywyQkFBMkI7UUFDakQsR0FBRyxDQUFDLGFBQWEsQ0FBQyxNQUFNLENBQUMsSUFBSSxDQUFDLElBQUksQ0FBQyxJQUFJLEVBQUUsT0FBTyxDQUFDLENBQUMsQ0FBQztRQUNuRCxHQUFHLENBQUMsYUFBYSxDQUFDLE1BQU0sQ0FBQyxJQUFJLENBQUMsSUFBSSxDQUFDLGtCQUFrQixFQUFFLE9BQU8sQ0FBQyxDQUFDLENBQUM7UUFDakUsR0FBRyxDQUFDLFdBQVcsQ0FBQyxJQUFJLENBQUMsSUFBSSxDQUFDLE1BQU0sQ0FBQyxDQUFDO1FBQ2xDLEdBQUcsQ0FBQyxVQUFVLENBQUMsQ0FBQyxDQUFDLE9BQU8sRUFBRSxDQUFDLENBQUM7UUFDNUIsT0FBTyxHQUFHLENBQUMsTUFBTSxFQUFFLENBQUM7SUFDdEIsQ0FBQztDQUNGO0FBakNELG9DQWlDQztBQVFEOzs7Ozs7O0dBT0c7QUFDSCxNQUFhLG1CQUFvQixTQUFRLFlBQVk7SUFDbkQsWUFBWSxrQkFBNkMsRUFBRSxHQUFXO1FBQ3BFLEtBQUssQ0FBQyxFQUFFLEVBQUUsa0JBQWtCLEVBQUUsQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDO0lBQ3ZDLENBQUM7Q0FDRjtBQUpELGtEQUlDIn0=