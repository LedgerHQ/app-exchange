"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.finalize = void 0;
const buffertools_1 = require("./buffertools");
const psbtv2_1 = require("./psbtv2");
/**
 * This roughly implements the "input finalizer" role of BIP370 (PSBTv2
 * https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki). However
 * the role is documented in BIP174 (PSBTv0
 * https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki).
 *
 * Verify that all inputs have a signature, and set inputFinalScriptwitness
 * and/or inputFinalScriptSig depending on the type of the spent outputs. Clean
 * fields that aren't useful anymore, partial signatures, redeem script and
 * derivation paths.
 *
 * @param psbt The psbt with all signatures added as partial sigs, either
 * through PSBT_IN_PARTIAL_SIG or PSBT_IN_TAP_KEY_SIG
 */
function finalize(psbt) {
    // First check that each input has a signature
    const inputCount = psbt.getGlobalInputCount();
    for (let i = 0; i < inputCount; i++) {
        const legacyPubkeys = psbt.getInputKeyDatas(i, psbtv2_1.psbtIn.PARTIAL_SIG);
        const taprootSig = psbt.getInputTapKeySig(i);
        if (legacyPubkeys.length == 0 && !taprootSig) {
            throw Error(`No signature for input ${i} present`);
        }
        if (legacyPubkeys.length > 0) {
            if (legacyPubkeys.length > 1) {
                throw Error(`Expected exactly one signature, got ${legacyPubkeys.length}`);
            }
            if (taprootSig) {
                throw Error('Both taproot and non-taproot signatures present.');
            }
            const isSegwitV0 = !!psbt.getInputWitnessUtxo(i);
            const redeemScript = psbt.getInputRedeemScript(i);
            const isWrappedSegwit = !!redeemScript;
            const signature = psbt.getInputPartialSig(i, legacyPubkeys[0]);
            if (!signature)
                throw new Error('Expected partial signature for input ' + i);
            if (isSegwitV0) {
                const witnessBuf = new buffertools_1.BufferWriter();
                witnessBuf.writeVarInt(2);
                witnessBuf.writeVarInt(signature.length);
                witnessBuf.writeSlice(signature);
                witnessBuf.writeVarInt(legacyPubkeys[0].length);
                witnessBuf.writeSlice(legacyPubkeys[0]);
                psbt.setInputFinalScriptwitness(i, witnessBuf.buffer());
                if (isWrappedSegwit) {
                    if (!redeemScript || redeemScript.length == 0) {
                        throw new Error("Expected non-empty redeemscript. Can't finalize intput " + i);
                    }
                    const scriptSigBuf = new buffertools_1.BufferWriter();
                    // Push redeemScript length
                    scriptSigBuf.writeUInt8(redeemScript.length);
                    scriptSigBuf.writeSlice(redeemScript);
                    psbt.setInputFinalScriptsig(i, scriptSigBuf.buffer());
                }
            }
            else {
                // Legacy input
                const scriptSig = new buffertools_1.BufferWriter();
                writePush(scriptSig, signature);
                writePush(scriptSig, legacyPubkeys[0]);
                psbt.setInputFinalScriptsig(i, scriptSig.buffer());
            }
        }
        else {
            // Taproot input
            const signature = psbt.getInputTapKeySig(i);
            if (!signature) {
                throw Error('No taproot signature found');
            }
            if (signature.length != 64 && signature.length != 65) {
                throw Error('Unexpected length of Schnorr signature.');
            }
            const witnessBuf = new buffertools_1.BufferWriter();
            witnessBuf.writeVarInt(1);
            witnessBuf.writeVarSlice(signature);
            psbt.setInputFinalScriptwitness(i, witnessBuf.buffer());
        }
        clearFinalizedInput(psbt, i);
    }
}
exports.finalize = finalize;
/**
 * Deletes fields that are no longer neccesary from the psbt.
 *
 * Note, the spec doesn't say anything about removing ouput fields
 * like PSBT_OUT_BIP32_DERIVATION_PATH and others, so we keep them
 * without actually knowing why. I think we should remove them too.
 */
function clearFinalizedInput(psbt, inputIndex) {
    const keyTypes = [
        psbtv2_1.psbtIn.BIP32_DERIVATION,
        psbtv2_1.psbtIn.PARTIAL_SIG,
        psbtv2_1.psbtIn.TAP_BIP32_DERIVATION,
        psbtv2_1.psbtIn.TAP_KEY_SIG,
    ];
    const witnessUtxoAvailable = !!psbt.getInputWitnessUtxo(inputIndex);
    const nonWitnessUtxoAvailable = !!psbt.getInputNonWitnessUtxo(inputIndex);
    if (witnessUtxoAvailable && nonWitnessUtxoAvailable) {
        // Remove NON_WITNESS_UTXO for segwit v0 as it's only needed while signing.
        // Segwit v1 doesn't have NON_WITNESS_UTXO set.
        // See https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki#cite_note-7
        keyTypes.push(psbtv2_1.psbtIn.NON_WITNESS_UTXO);
    }
    psbt.deleteInputEntries(inputIndex, keyTypes);
}
/**
 * Writes a script push operation to buf, which looks different
 * depending on the size of the data. See
 * https://en.bitcoin.it/wiki/Script#Constants
 *
 * @param buf the BufferWriter to write to
 * @param data the Buffer to be pushed.
 */
function writePush(buf, data) {
    if (data.length <= 75) {
        buf.writeUInt8(data.length);
    }
    else if (data.length <= 256) {
        buf.writeUInt8(76);
        buf.writeUInt8(data.length);
    }
    else if (data.length <= 256 * 256) {
        buf.writeUInt8(77);
        const b = Buffer.alloc(2);
        b.writeUInt16LE(data.length, 0);
        buf.writeSlice(b);
    }
    buf.writeSlice(data);
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicHNidEZpbmFsaXplci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvcHNidEZpbmFsaXplci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7QUFBQSwrQ0FBNkM7QUFDN0MscUNBQTBDO0FBRTFDOzs7Ozs7Ozs7Ozs7O0dBYUc7QUFDSCxTQUFnQixRQUFRLENBQUMsSUFBWTtJQUNuQyw4Q0FBOEM7SUFDOUMsTUFBTSxVQUFVLEdBQUcsSUFBSSxDQUFDLG1CQUFtQixFQUFFLENBQUM7SUFDOUMsS0FBSyxJQUFJLENBQUMsR0FBRyxDQUFDLEVBQUUsQ0FBQyxHQUFHLFVBQVUsRUFBRSxDQUFDLEVBQUUsRUFBRTtRQUNuQyxNQUFNLGFBQWEsR0FBRyxJQUFJLENBQUMsZ0JBQWdCLENBQUMsQ0FBQyxFQUFFLGVBQU0sQ0FBQyxXQUFXLENBQUMsQ0FBQztRQUNuRSxNQUFNLFVBQVUsR0FBRyxJQUFJLENBQUMsaUJBQWlCLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDN0MsSUFBSSxhQUFhLENBQUMsTUFBTSxJQUFJLENBQUMsSUFBSSxDQUFDLFVBQVUsRUFBRTtZQUM1QyxNQUFNLEtBQUssQ0FBQywwQkFBMEIsQ0FBQyxVQUFVLENBQUMsQ0FBQztTQUNwRDtRQUNELElBQUksYUFBYSxDQUFDLE1BQU0sR0FBRyxDQUFDLEVBQUU7WUFDNUIsSUFBSSxhQUFhLENBQUMsTUFBTSxHQUFHLENBQUMsRUFBRTtnQkFDNUIsTUFBTSxLQUFLLENBQ1QsdUNBQXVDLGFBQWEsQ0FBQyxNQUFNLEVBQUUsQ0FDOUQsQ0FBQzthQUNIO1lBQ0QsSUFBSSxVQUFVLEVBQUU7Z0JBQ2QsTUFBTSxLQUFLLENBQUMsa0RBQWtELENBQUMsQ0FBQzthQUNqRTtZQUVELE1BQU0sVUFBVSxHQUFHLENBQUMsQ0FBQyxJQUFJLENBQUMsbUJBQW1CLENBQUMsQ0FBQyxDQUFDLENBQUM7WUFDakQsTUFBTSxZQUFZLEdBQUcsSUFBSSxDQUFDLG9CQUFvQixDQUFD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