"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AppClient = void 0;
const bip32_1 = require("./bip32");
const clientCommands_1 = require("./clientCommands");
const merkelizedPsbt_1 = require("./merkelizedPsbt");
const merkle_1 = require("./merkle");
const varint_1 = require("./varint");
const CLA_BTC = 0xe1;
const CLA_FRAMEWORK = 0xf8;
var BitcoinIns;
(function (BitcoinIns) {
    BitcoinIns[BitcoinIns["GET_PUBKEY"] = 0] = "GET_PUBKEY";
    BitcoinIns[BitcoinIns["REGISTER_WALLET"] = 2] = "REGISTER_WALLET";
    BitcoinIns[BitcoinIns["GET_WALLET_ADDRESS"] = 3] = "GET_WALLET_ADDRESS";
    BitcoinIns[BitcoinIns["SIGN_PSBT"] = 4] = "SIGN_PSBT";
    BitcoinIns[BitcoinIns["GET_MASTER_FINGERPRINT"] = 5] = "GET_MASTER_FINGERPRINT";
    BitcoinIns[BitcoinIns["SIGN_MESSAGE"] = 16] = "SIGN_MESSAGE";
})(BitcoinIns || (BitcoinIns = {}));
var FrameworkIns;
(function (FrameworkIns) {
    FrameworkIns[FrameworkIns["CONTINUE_INTERRUPTED"] = 1] = "CONTINUE_INTERRUPTED";
})(FrameworkIns || (FrameworkIns = {}));
/**
 * This class encapsulates the APDU protocol documented at
 * https://github.com/LedgerHQ/app-bitcoin-new/blob/master/doc/bitcoin.md
 */
class AppClient {
    constructor(transport) {
        this.transport = transport;
    }
    async makeRequest(ins, data, cci) {
        let response = await this.transport.send(CLA_BTC, ins, 0, 0, data, [0x9000, 0xe000]);
        while (response.readUInt16BE(response.length - 2) === 0xe000) {
            if (!cci) {
                throw new Error('Unexpected SW_INTERRUPTED_EXECUTION');
            }
            const hwRequest = response.slice(0, -2);
            const commandResponse = cci.execute(hwRequest);
            response = await this.transport.send(CLA_FRAMEWORK, FrameworkIns.CONTINUE_INTERRUPTED, 0, 0, commandResponse, [0x9000, 0xe000]);
        }
        return response.slice(0, -2); // drop the status word (can only be 0x9000 at this point)
    }
    async getExtendedPubkey(display, pathElements) {
        if (pathElements.length > 6) {
            throw new Error('Path too long. At most 6 levels allowed.');
        }
        const response = await this.makeRequest(BitcoinIns.GET_PUBKEY, Buffer.concat([
            Buffer.from(display ? [1] : [0]),
            (0, bip32_1.pathElementsToBuffer)(pathElements),
        ]));
        return response.toString('ascii');
    }
    async registerWallet(walletPolicy) {
        const serializedWalletPolicy = walletPolicy.serialize();
        const clientInterpreter = new clientCommands_1.ClientCommandInterpreter();
        clientInterpreter.addKnownPreimage(serializedWalletPolicy);
        clientInterpreter.addKnownList(walletPolicy.keys.map((k) => Buffer.from(k, 'ascii')));
        const response = await this.makeRequest(BitcoinIns.REGISTER_WALLET, Buffer.concat([
            (0, varint_1.createVarint)(serializedWalletPolicy.length),
            serializedWalletPolicy,
        ]), clientInterpreter);
        if (response.length != 64) {
            throw Error(`Invalid response length. Expected 64 bytes, got ${response.length}`);
        }
        return [response.subarray(0, 32), response.subarray(32)];
    }
    async getWalletAddress(walletPolicy, walletHMAC, change, addressIndex, display) {
        if (change !== 0 && change !== 1)
            throw new Error('Change can only be 0 or 1');
        if (addressIndex < 0 || !Number.isInteger(addressIndex))
            throw new Error('Invalid address index');
        if (walletHMAC != null && walletHMAC.length != 32) {
            throw new Error('Invalid HMAC length');
        }
        const clientInterpreter = new clientCommands_1.ClientCommandInterpreter();
        clientInterpreter.addKnownList(walletPolicy.keys.map((k) => Buffer.from(k, 'ascii')));
        clientInterpreter.addKnownPreimage(walletPolicy.serialize());
        const addressIndexBuffer = Buffer.alloc(4);
        addressIndexBuffer.writeUInt32BE(addressIndex, 0);
        const response = await this.makeRequest(BitcoinIns.GET_WALLET_ADDRESS, Buffer.concat([
            Buffer.from(display ? [1] : [0]),
            walletPolicy.getWalletId(),
            walletHMAC || Buffer.alloc(32, 0),
            Buffer.from([change]),
            addressIndexBuffer,
        ]), clientInterpreter);
        return response.toString('ascii');
    }
    async signPsbt(psbt, walletPolicy, walletHMAC, progressCallback) {
        const merkelizedPsbt = new merkelizedPsbt_1.MerkelizedPsbt(psbt);
        if (walletHMAC != null && walletHMAC.length != 32) {
            throw new Error('Invalid HMAC length');
        }
        const clientInterpreter = new clientCommands_1.ClientCommandInterpreter(progressCallback);
        // prepare ClientCommandInterpreter
        clientInterpreter.addKnownList(walletPolicy.keys.map((k) => Buffer.from(k, 'ascii')));
        clientInterpreter.addKnownPreimage(walletPolicy.serialize());
        clientInterpreter.addKnownMapping(merkelizedPsbt.globalMerkleMap);
        for (const map of merkelizedPsbt.inputMerkleMaps) {
            clientInterpreter.addKnownMapping(map);
        }
        for (const map of merkelizedPsbt.outputMerkleMaps) {
            clientInterpreter.addKnownMapping(map);
        }
        clientInterpreter.addKnownList(merkelizedPsbt.inputMapCommitments);
        const inputMapsRoot = new merkle_1.Merkle(merkelizedPsbt.inputMapCommitments.map((m) => (0, merkle_1.hashLeaf)(m))).getRoot();
        clientInterpreter.addKnownList(merkelizedPsbt.outputMapCommitments);
        const outputMapsRoot = new merkle_1.Merkle(merkelizedPsbt.outputMapCommitments.map((m) => (0, merkle_1.hashLeaf)(m))).getRoot();
        await this.makeRequest(BitcoinIns.SIGN_PSBT, Buffer.concat([
            merkelizedPsbt.getGlobalKeysValuesRoot(),
            (0, varint_1.createVarint)(merkelizedPsbt.getGlobalInputCount()),
            inputMapsRoot,
            (0, varint_1.createVarint)(merkelizedPsbt.getGlobalOutputCount()),
            outputMapsRoot,
            walletPolicy.getWalletId(),
            walletHMAC || Buffer.alloc(32, 0),
        ]), clientInterpreter);
        const yielded = clientInterpreter.getYielded();
        const ret = new Map();
        for (const inputAndSig of yielded) {
            ret.set(inputAndSig[0], inputAndSig.slice(1));
        }
        return ret;
    }
    async getMasterFingerprint() {
        return this.makeRequest(BitcoinIns.GET_MASTER_FINGERPRINT, Buffer.from([]));
    }
    async signMessage(message, pathElements) {
        const clientInterpreter = new clientCommands_1.ClientCommandInterpreter();
        // prepare ClientCommandInterpreter
        const nChunks = Math.ceil(message.length / 64);
        const chunks = [];
        for (let i = 0; i < nChunks; i++) {
            chunks.push(message.subarray(64 * i, 64 * i + 64));
        }
        clientInterpreter.addKnownList(chunks);
        const chunksRoot = new merkle_1.Merkle(chunks.map((m) => (0, merkle_1.hashLeaf)(m))).getRoot();
        const result = await this.makeRequest(BitcoinIns.SIGN_MESSAGE, Buffer.concat([
            (0, bip32_1.pathElementsToBuffer)(pathElements),
            (0, varint_1.createVarint)(message.length),
            chunksRoot,
        ]), clientInterpreter);
        return result.toString('base64');
    }
}
exports.AppClient = AppClient;
exports.default = AppClient;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiYXBwQ2xpZW50LmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9hcHBDbGllbnQudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBRUEsbUNBQStDO0FBQy9DLHFEQUE0RDtBQUM1RCxxREFBa0Q7QUFDbEQscUNBQTRDO0FBRzVDLHFDQUF3QztBQUV4QyxNQUFNLE9BQU8sR0FBRyxJQUFJLENBQUM7QUFDckIsTUFBTSxhQUFhLEdBQUcsSUFBSSxDQUFDO0FBRTNCLElBQUssVUFPSjtBQVBELFdBQUssVUFBVTtJQUNiLHVEQUFpQixDQUFBO0lBQ2pCLGlFQUFzQixDQUFBO0lBQ3RCLHVFQUF5QixDQUFBO0lBQ3pCLHFEQUFnQixDQUFBO0lBQ2hCLCtFQUE2QixDQUFBO0lBQzdCLDREQUFtQixDQUFBO0FBQ3JCLENBQUMsRUFQSSxVQUFVLEtBQVYsVUFBVSxRQU9kO0FBRUQsSUFBSyxZQUVKO0FBRkQsV0FBSyxZQUFZO0lBQ2YsK0VBQTJCLENBQUE7QUFDN0IsQ0FBQyxFQUZJLFlBQVksS0FBWixZQUFZLFFBRWhCO0FBRUQ7OztHQUdHO0FBQ0gsTUFBYSxTQUFTO0lBR3BCLFlBQVksU0FBb0I7UUFDOUIsSUFBSSxDQUFDLFNBQVMsR0FBRyxTQUFTLENBQUM7SUFDN0IsQ0FBQztJQUVPLEtBQUssQ0FBQyxXQUFXLENBQ3ZCLEdBQWUsRUFDZixJQUFZLEVBQ1osR0FBOEI7UUFFOUIsSUFBSSxRQUFRLEdBQVcsTUFBTSxJQUFJLENBQUMsU0FBUyxDQUFDLElBQUksQ0FDOUMsT0FBTyxFQUNQLEdBQUcsRUFDSCxDQUFDLEVBQ0QsQ0FBQyxFQUNELElBQUksRUFDSixDQUFDLE1BQU0sRUFBRSxNQUFNLENBQUMsQ0FDakIsQ0FBQztRQUNGLE9BQU8sUUFBUSxDQUFDLFlBQVksQ0FBQyxRQUFRLENBQUMsTUFBTSxHQUFHLENBQUMsQ0FBQyxLQUFLLE1BQU0sRUFBRTtZQUM1RCxJQUFJLENBQUMsR0FBRyxFQUFFO2dCQUNSLE1B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