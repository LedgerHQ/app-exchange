/// <reference types="node" />
import Transport from '@ledgerhq/hw-transport';
import { WalletPolicy } from './policy';
import { PsbtV2 } from './psbtv2';
/**
 * This class encapsulates the APDU protocol documented at
 * https://github.com/LedgerHQ/app-bitcoin-new/blob/master/doc/bitcoin.md
 */
export declare class AppClient {
    readonly transport: Transport;
    constructor(transport: Transport);
    private makeRequest;
    getExtendedPubkey(display: boolean, pathElements: readonly number[]): Promise<string>;
    registerWallet(walletPolicy: WalletPolicy): Promise<readonly [Buffer, Buffer]>;
    getWalletAddress(walletPolicy: WalletPolicy, walletHMAC: Buffer | null, change: number, addressIndex: number, display: boolean): Promise<string>;
    signPsbt(psbt: PsbtV2, walletPolicy: WalletPolicy, walletHMAC: Buffer | null, progressCallback?: () => void): Promise<Map<number, Buffer>>;
    getMasterFingerprint(): Promise<Buffer>;
    signMessage(message: Buffer, pathElements: readonly number[]): Promise<string>;
}
export default AppClient;
