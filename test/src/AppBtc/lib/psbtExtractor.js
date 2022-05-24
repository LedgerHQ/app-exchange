"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.extract = void 0;
const buffertools_1 = require("./buffertools");
/**
 * This implements the "Transaction Extractor" role of BIP370 (PSBTv2
 * https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki#transaction-extractor). However
 * the role is partially documented in BIP174 (PSBTv0
 * https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki#transaction-extractor).
 */
function extract(psbt) {
    var _a, _b;
    const tx = new buffertools_1.BufferWriter();
    tx.writeUInt32(psbt.getGlobalTxVersion());
    const isSegwit = !!psbt.getInputWitnessUtxo(0);
    if (isSegwit) {
        tx.writeSlice(Buffer.from([0, 1]));
    }
    const inputCount = psbt.getGlobalInputCount();
    tx.writeVarInt(inputCount);
    const witnessWriter = new buffertools_1.BufferWriter();
    for (let i = 0; i < inputCount; i++) {
        tx.writeSlice(psbt.getInputPreviousTxid(i));
        tx.writeUInt32(psbt.getInputOutputIndex(i));
        tx.writeVarSlice((_a = psbt.getInputFinalScriptsig(i)) !== null && _a !== void 0 ? _a : Buffer.from([]));
        tx.writeUInt32(psbt.getInputSequence(i));
        if (isSegwit) {
            witnessWriter.writeSlice(psbt.getInputFinalScriptwitness(i));
        }
    }
    const outputCount = psbt.getGlobalOutputCount();
    tx.writeVarInt(outputCount);
    for (let i = 0; i < outputCount; i++) {
        tx.writeUInt64(psbt.getOutputAmount(i));
        tx.writeVarSlice(psbt.getOutputScript(i));
    }
    tx.writeSlice(witnessWriter.buffer());
    tx.writeUInt32((_b = psbt.getGlobalFallbackLocktime()) !== null && _b !== void 0 ? _b : 0);
    return tx.buffer();
}
exports.extract = extract;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoicHNidEV4dHJhY3Rvci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvcHNidEV4dHJhY3Rvci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7QUFBQSwrQ0FBNkM7QUFHN0M7Ozs7O0dBS0c7QUFDSCxTQUFnQixPQUFPLENBQUMsSUFBWTs7SUFDbEMsTUFBTSxFQUFFLEdBQUcsSUFBSSwwQkFBWSxFQUFFLENBQUM7SUFDOUIsRUFBRSxDQUFDLFdBQVcsQ0FBQyxJQUFJLENBQUMsa0JBQWtCLEVBQUUsQ0FBQyxDQUFDO0lBRTFDLE1BQU0sUUFBUSxHQUFHLENBQUMsQ0FBQyxJQUFJLENBQUMsbUJBQW1CLENBQUMsQ0FBQyxDQUFDLENBQUM7SUFDL0MsSUFBSSxRQUFRLEVBQUU7UUFDWixFQUFFLENBQUMsVUFBVSxDQUFDLE1BQU0sQ0FBQyxJQUFJLENBQUMsQ0FBQyxDQUFDLEVBQUUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0tBQ3BDO0lBQ0QsTUFBTSxVQUFVLEdBQUcsSUFBSSxDQUFDLG1CQUFtQixFQUFFLENBQUM7SUFDOUMsRUFBRSxDQUFDLFdBQVcsQ0FBQyxVQUFVLENBQUMsQ0FBQztJQUMzQixNQUFNLGFBQWEsR0FBRyxJQUFJLDBCQUFZLEVBQUUsQ0FBQztJQUN6QyxLQUFLLElBQUksQ0FBQyxHQUFHLENBQUMsRUFBRSxDQUFDLEdBQUcsVUFBVSxFQUFFLENBQUMsRUFBRSxFQUFFO1FBQ25DLEVBQUUsQ0FBQyxVQUFVLENBQUMsSUFBSSxDQUFDLG9CQUFvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDNUMsRUFBRSxDQUFDLFdBQVcsQ0FBQyxJQUFJLENBQUMsbUJBQW1CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztRQUM1QyxFQUFFLENBQUMsYUFBYSxDQUFDLE1BQUEsSUFBSSxDQUFDLHNCQUFzQixDQUFDLENBQUMsQ0FBQyxtQ0FBSSxNQUFNLENBQUMsSUFBSSxDQUFDLEVBQUUsQ0FBQyxDQUFDLENBQUM7UUFDcEUsRUFBRSxDQUFDLFdBQVcsQ0FBQyxJQUFJLENBQUMsZ0JBQWdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztRQUN6QyxJQUFJLFFBQVEsRUFBRTtZQUNaLGFBQWEsQ0FBQyxVQUFVLENBQUMsSUFBSSxDQUFDLDBCQUEwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7U0FDOUQ7S0FDRjtJQUNELE1BQU0sV0FBVyxHQUFHLElBQUksQ0FBQyxvQkFBb0IsRUFBRSxDQUFDO0lBQ2hELEVBQUUsQ0FBQyxXQUFXLENBQUMsV0FBVyxDQUFDLENBQUM7SUFDNUIsS0FBSyxJQUFJLENBQUMsR0FBRyxDQUFDLEVBQUUsQ0FBQyxHQUFHLFdBQVcsRUFBRSxDQUFDLEVBQUUsRUFBRTtRQUNwQyxFQUFFLENBQUMsV0FBVyxDQUFDLElBQUksQ0FBQyxlQUFlLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztRQUN4QyxFQUFFLENBQUMsYUFBYSxDQUFDLElBQUksQ0FBQyxlQUFlLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztLQUMzQztJQUNELEVBQUUsQ0FBQyxVQUFVLENBQUMsYUFBYSxDQUFDLE1BQU0sRUFBRSxDQUFDLENBQUM7SUFDdEMsRUFBRSxDQUFDLFdBQVcsQ0FBQyxNQUFBLElBQUksQ0FBQyx5QkFBeUIsRUFBRSxtQ0FBSSxDQUFDLENBQUMsQ0FBQztJQUN0RCxPQUFPLEVBQUUsQ0FBQyxNQUFNLEVBQUUsQ0FBQztBQUNyQixDQUFDO0FBN0JELDBCQTZCQyJ9