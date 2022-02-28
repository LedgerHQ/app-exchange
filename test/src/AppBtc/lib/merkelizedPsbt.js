"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MerkelizedPsbt = void 0;
const merkleMap_1 = require("./merkleMap");
const psbtv2_1 = require("./psbtv2");
/**
 * This class merkelizes a PSBTv2, by merkelizing the different
 * maps of the psbt. This is used during the transaction signing process,
 * where the hardware app can request specific parts of the psbt from the
 * client code and be sure that the response data actually belong to the psbt.
 * The reason for this is the limited amount of memory available to the app,
 * so it can't always store the full psbt in memory.
 *
 * The signing process is documented at
 * https://github.com/LedgerHQ/app-bitcoin-new/blob/master/doc/bitcoin.md#sign_psbt
 */
class MerkelizedPsbt extends psbtv2_1.PsbtV2 {
    constructor(psbt) {
        super();
        this.inputMerkleMaps = [];
        this.outputMerkleMaps = [];
        psbt.copy(this);
        this.globalMerkleMap = MerkelizedPsbt.createMerkleMap(this.globalMap);
        for (let i = 0; i < this.getGlobalInputCount(); i++) {
            this.inputMerkleMaps.push(MerkelizedPsbt.createMerkleMap(this.inputMaps[i]));
        }
        this.inputMapCommitments = [...this.inputMerkleMaps.values()].map((v) => v.commitment());
        for (let i = 0; i < this.getGlobalOutputCount(); i++) {
            this.outputMerkleMaps.push(MerkelizedPsbt.createMerkleMap(this.outputMaps[i]));
        }
        this.outputMapCommitments = [...this.outputMerkleMaps.values()].map((v) => v.commitment());
    }
    // These public functions are for MerkelizedPsbt.
    getGlobalSize() {
        return this.globalMap.size;
    }
    getGlobalKeysValuesRoot() {
        return this.globalMerkleMap.commitment();
    }
    static createMerkleMap(map) {
        const sortedKeysStrings = [...map.keys()].sort();
        const values = sortedKeysStrings.map((k) => {
            const v = map.get(k);
            if (!v) {
                throw new Error('No value for key ' + k);
            }
            return v;
        });
        const sortedKeys = sortedKeysStrings.map((k) => Buffer.from(k, 'hex'));
        return new merkleMap_1.MerkleMap(sortedKeys, values);
    }
}
exports.MerkelizedPsbt = MerkelizedPsbt;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoibWVya2VsaXplZFBzYnQuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvbGliL21lcmtlbGl6ZWRQc2J0LnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7OztBQUFBLDJDQUF3QztBQUN4QyxxQ0FBa0M7QUFFbEM7Ozs7Ozs7Ozs7R0FVRztBQUNILE1BQWEsY0FBZSxTQUFRLGVBQU07SUFNeEMsWUFBWSxJQUFZO1FBQ3RCLEtBQUssRUFBRSxDQUFDO1FBTEgsb0JBQWUsR0FBZ0IsRUFBRSxDQUFDO1FBQ2xDLHFCQUFnQixHQUFnQixFQUFFLENBQUM7UUFLeEMsSUFBSSxDQUFDLElBQUksQ0FBQyxJQUFJLENBQUMsQ0FBQztRQUNoQixJQUFJLENBQUMsZUFBZSxHQUFHLGNBQWMsQ0FBQyxlQUFlLENBQUMsSUFBSSxDQUFDLFNBQVMsQ0FBQyxDQUFDO1FBRXRFLEtBQUssSUFBSSxDQUFDLEdBQUcsQ0FBQyxFQUFFLENBQUMsR0FBRyxJQUFJLENBQUMsbUJBQW1CLEVBQUUsRUFBRSxDQUFDLEVBQUUsRUFBRTtZQUNuRCxJQUFJLENBQUMsZUFBZSxDQUFDLElBQUksQ0FDdkIsY0FBYyxDQUFDLGVBQWUsQ0FBQyxJQUFJLENBQUMsU0FBUyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQ2xELENBQUM7U0FDSDtRQUNELElBQUksQ0FBQyxtQkFBbUIsR0FBRyxDQUFDLEdBQUcsSUFBSSxDQUFDLGVBQWUsQ0FBQyxNQUFNLEVBQUUsQ0FBQyxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUMsRUFBRSxFQUFFLENBQ3RFLENBQUMsQ0FBQyxVQUFVLEVBQUUsQ0FDZixDQUFDO1FBRUYsS0FBSyxJQUFJLENBQUMsR0FBRyxDQUFDLEVBQUUsQ0FBQyxHQUFHLElBQUksQ0FBQyxvQkFBb0IsRUFBRSxFQUFFLENBQUMsRUFBRSxFQUFFO1lBQ3BELElBQUksQ0FBQyxnQkFBZ0IsQ0FBQyxJQUFJLENBQ3hCLGNBQWMsQ0FBQyxlQUFlLENBQUMsSUFBSSxDQUFDLFVBQVUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUNuRCxDQUFDO1NBQ0g7UUFDRCxJQUFJLENBQUMsb0JBQW9CLEdBQUcsQ0FBQyxHQUFHLElBQUksQ0FBQyxnQkFBZ0IsQ0FBQyxNQUFNLEVBQUUsQ0FBQyxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUMsRUFBRSxFQUFFLENBQ3hFLENBQUMsQ0FBQyxVQUFVLEVBQUUsQ0FDZixDQUFDO0lBQ0osQ0FBQztJQUNELGlEQUFpRDtJQUNqRCxhQUFhO1FBQ1gsT0FBTyxJQUFJLENBQUMsU0FBUyxDQUFDLElBQUksQ0FBQztJQUM3QixDQUFDO0lBQ0QsdUJBQXVCO1FBQ3JCLE9BQU8sSUFBSSxDQUFDLGVBQWUsQ0FBQyxVQUFVLEVBQUUsQ0FBQztJQUMzQyxDQUFDO0lBRU8sTUFBTSxDQUFDLGVBQWUsQ0FBQyxHQUFnQztRQUM3RCxNQUFNLGlCQUFpQixHQUFHLENBQUMsR0FBRyxHQUFHLENBQUMsSUFBSSxFQUFFLENBQUMsQ0FBQyxJQUFJLEVBQUUsQ0FBQztRQUNqRCxNQUFNLE1BQU0sR0FBRyxpQkFBaUIsQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDLEVBQUUsRUFBRTtZQUN6QyxNQUFNLENBQUMsR0FBRyxHQUFHLENBQUMsR0FBRyxDQUFDLENBQUMsQ0FBQyxDQUFDO1lBQ3JCLElBQUksQ0FBQyxDQUFDLEVBQUU7Z0JBQ04sTUFBTSxJQUFJLEtBQUssQ0FBQyxtQkFBbUIsR0FBRyxDQUFDLENBQUMsQ0FBQzthQUMxQztZQUNELE9BQU8sQ0FBQyxDQUFDO1FBQ1gsQ0FBQyxDQUFDLENBQUM7UUFDSCxNQUFNLFVBQVUsR0FBRyxpQkFBaUIsQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDLEVBQUUsRUFBRSxDQUFDLE1BQU0sQ0FBQyxJQUFJLENBQUMsQ0FBQyxFQUFFLEtBQUssQ0FBQyxDQUFDLENBQUM7UUFFdkUsT0FBTyxJQUFJLHFCQUFTLENBQUMsVUFBVSxFQUFFLE1BQU0sQ0FBQyxDQUFDO0lBQzNDLENBQUM7Q0FDRjtBQWxERCx3Q0FrREMifQ==