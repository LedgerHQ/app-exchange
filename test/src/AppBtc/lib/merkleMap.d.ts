/// <reference types="node" />
import { Merkle } from './merkle';
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
export declare class MerkleMap {
    readonly keys: readonly Buffer[];
    readonly keysTree: Merkle;
    readonly values: readonly Buffer[];
    readonly valuesTree: Merkle;
    /**
     * @param keys Sorted list of (unhashed) keys
     * @param values values, in corresponding order as the keys, and of equal length
     */
    constructor(keys: readonly Buffer[], values: readonly Buffer[]);
    commitment(): Buffer;
}
