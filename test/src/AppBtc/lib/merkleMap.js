"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MerkleMap = void 0;
const merkle_1 = require("./merkle");
const varint_1 = require("./varint");
/**
 * This implements "Merkelized Maps", documented at
 * https://github.com/LedgerHQ/app-bitcoin-new/blob/master/doc/merkle.md#merkleized-maps
 *
 * A merkelized map consist of two merkle trees, one for the keys of
 * a map and one for the values of the same map, thus the two merkle
 * trees have the same shape. The commitment is the number elements
 * in the map followed by the keys' merkle root followed by the
 * values' merkle root.
 */
class MerkleMap {
    /**
     * @param keys Sorted list of (unhashed) keys
     * @param values values, in corresponding order as the keys, and of equal length
     */
    constructor(keys, values) {
        if (keys.length != values.length) {
            throw new Error('keys and values should have the same length');
        }
        // Sanity check: verify that keys are actually sorted and with no duplicates
        for (let i = 0; i < keys.length - 1; i++) {
            if (keys[i].toString('hex') >= keys[i + 1].toString('hex')) {
                throw new Error('keys must be in strictly increasing order');
            }
        }
        this.keys = keys;
        this.keysTree = new merkle_1.Merkle(keys.map((k) => (0, merkle_1.hashLeaf)(k)));
        this.values = values;
        this.valuesTree = new merkle_1.Merkle(values.map((v) => (0, merkle_1.hashLeaf)(v)));
    }
    commitment() {
        // returns a buffer between 65 and 73 (included) bytes long
        return Buffer.concat([
            (0, varint_1.createVarint)(this.keys.length),
            this.keysTree.getRoot(),
            this.valuesTree.getRoot(),
        ]);
    }
}
exports.MerkleMap = MerkleMap;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoibWVya2xlTWFwLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vLi4vLi4vc3JjL2xpYi9tZXJrbGVNYXAudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7O0FBQUEscUNBQTRDO0FBQzVDLHFDQUF3QztBQUV4Qzs7Ozs7Ozs7O0dBU0c7QUFDSCxNQUFhLFNBQVM7SUFLcEI7OztPQUdHO0lBQ0gsWUFBWSxJQUF1QixFQUFFLE1BQXlCO1FBQzVELElBQUksSUFBSSxDQUFDLE1BQU0sSUFBSSxNQUFNLENBQUMsTUFBTSxFQUFFO1lBQ2hDLE1BQU0sSUFBSSxLQUFLLENBQUMsNkNBQTZDLENBQUMsQ0FBQztTQUNoRTtRQUVELDRFQUE0RTtRQUM1RSxLQUFLLElBQUksQ0FBQyxHQUFHLENBQUMsRUFBRSxDQUFDLEdBQUcsSUFBSSxDQUFDLE1BQU0sR0FBRyxDQUFDLEVBQUUsQ0FBQyxFQUFFLEVBQUU7WUFDeEMsSUFBSSxJQUFJLENBQUMsQ0FBQyxDQUFDLENBQUMsUUFBUSxDQUFDLEtBQUssQ0FBQyxJQUFJLElBQUksQ0FBQyxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUMsUUFBUSxDQUFDLEtBQUssQ0FBQyxFQUFFO2dCQUMxRCxNQUFNLElBQUksS0FBSyxDQUFDLDJDQUEyQyxDQUFDLENBQUM7YUFDOUQ7U0FDRjtRQUVELElBQUksQ0FBQyxJQUFJLEdBQUcsSUFBSSxDQUFDO1FBQ2pCLElBQUksQ0FBQyxRQUFRLEdBQUcsSUFBSSxlQUFNLENBQUMsSUFBSSxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUMsRUFBRSxFQUFFLENBQUMsSUFBQSxpQkFBUSxFQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztRQUN6RCxJQUFJLENBQUMsTUFBTSxHQUFHLE1BQU0sQ0FBQztRQUNyQixJQUFJLENBQUMsVUFBVSxHQUFHLElBQUksZUFBTSxDQUFDLE1BQU0sQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDLEVBQUUsRUFBRSxDQUFDLElBQUEsaUJBQVEsRUFBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7SUFDL0QsQ0FBQztJQUVELFVBQVU7UUFDUiwyREFBMkQ7UUFDM0QsT0FBTyxNQUFNLENBQUMsTUFBTSxDQUFDO1lBQ25CLElBQUEscUJBQVksRUFBQyxJQUFJLENBQUMsSUFBSSxDQUFDLE1BQU0sQ0FBQztZQUM5QixJQUFJLENBQUMsUUFBUSxDQUFDLE9BQU8sRUFBRTtZQUN2QixJQUFJLENBQUMsVUFBVSxDQUFDLE9BQU8sRUFBRTtTQUMxQixDQUFDLENBQUM7SUFDTCxDQUFDO0NBQ0Y7QUFuQ0QsOEJBbUNDIn0=