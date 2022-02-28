/// <reference types="node" />
import { Merkle } from './merkle';
import { MerkleMap } from './merkleMap';
declare enum ClientCommandCode {
    YIELD = 16,
    GET_PREIMAGE = 64,
    GET_MERKLE_LEAF_PROOF = 65,
    GET_MERKLE_LEAF_INDEX = 66,
    GET_MORE_ELEMENTS = 160
}
declare abstract class ClientCommand {
    abstract code: ClientCommandCode;
    abstract execute(request: Buffer): Buffer;
}
export declare class YieldCommand extends ClientCommand {
    private readonly progressCallback?;
    private results;
    readonly code = ClientCommandCode.YIELD;
    constructor(results: Buffer[], progressCallback?: () => void);
    execute(request: Buffer): Buffer;
}
export declare class GetPreimageCommand extends ClientCommand {
    private readonly known_preimages;
    private queue;
    readonly code = ClientCommandCode.GET_PREIMAGE;
    constructor(known_preimages: ReadonlyMap<string, Buffer>, queue: Buffer[]);
    execute(request: Buffer): Buffer;
}
export declare class GetMerkleLeafProofCommand extends ClientCommand {
    private readonly known_trees;
    private queue;
    readonly code = ClientCommandCode.GET_MERKLE_LEAF_PROOF;
    constructor(known_trees: ReadonlyMap<string, Merkle>, queue: Buffer[]);
    execute(request: Buffer): Buffer;
}
export declare class GetMerkleLeafIndexCommand extends ClientCommand {
    private readonly known_trees;
    readonly code = ClientCommandCode.GET_MERKLE_LEAF_INDEX;
    constructor(known_trees: ReadonlyMap<string, Merkle>);
    execute(request: Buffer): Buffer;
}
export declare class GetMoreElementsCommand extends ClientCommand {
    queue: Buffer[];
    readonly code = ClientCommandCode.GET_MORE_ELEMENTS;
    constructor(queue: Buffer[]);
    execute(request: Buffer): Buffer;
}
/**
 * This class will dispatch a client command coming from the hardware device to
 * the appropriate client command implementation. Those client commands
 * typically requests data from a merkle tree or merkelized maps.
 *
 * A ClientCommandInterpreter is prepared by adding the merkle trees and
 * merkelized maps it should be able to serve to the hardware device. This class
 * doesn't know anything about the semantics of the data it holds, it just
 * serves merkle data. It doesn't even know in what context it is being
 * executed, ie SignPsbt, getWalletAddress, etc.
 *
 * If the command yelds results to the client, as signPsbt does, the yielded
 * data will be accessible after the command completed by calling getYielded(),
 * which will return the yields in the same order as they came in.
 */
export declare class ClientCommandInterpreter {
    private readonly roots;
    private readonly preimages;
    private yielded;
    private queue;
    private readonly commands;
    constructor(progressCallback?: () => void);
    getYielded(): readonly Buffer[];
    addKnownPreimage(preimage: Buffer): void;
    addKnownList(elements: readonly Buffer[]): void;
    addKnownMapping(mm: MerkleMap): void;
    execute(request: Buffer): Buffer;
}
export {};
