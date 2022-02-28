/// <reference types="node" />
export declare function parseVarint(data: Buffer, offset: number): readonly [bigint, number];
export declare function createVarint(value: number | bigint): Buffer;
export declare function sanitizeVarintToNumber(n: bigint): number;
