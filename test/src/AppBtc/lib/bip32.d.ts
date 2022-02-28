/// <reference types="node" />
export declare function pathElementsToBuffer(paths: readonly number[]): Buffer;
export declare function bip32asBuffer(path: string): Buffer;
export declare function pathArrayToString(pathElements: readonly number[]): string;
export declare function pathStringToArray(path: string): readonly number[];
export declare function pubkeyFromXpub(xpub: string): Buffer;
export declare function getXpubComponents(xpub: string): {
    readonly chaincode: Buffer;
    readonly pubkey: Buffer;
    readonly version: number;
};
export declare function hardenedPathOf(pathElements: readonly number[]): readonly number[];
