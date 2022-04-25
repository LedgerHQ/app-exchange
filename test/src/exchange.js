// @flow
import type Transport from "@ledgerhq/hw-transport";
import { BigNumber } from "bignumber.js";
import { TransportStatusError } from "@ledgerhq/errors";
import invariant from "invariant";
import { COMMAND, RESULT } from "Swap.js";

export const TRANSACTION_RATES = {
    FIXED: 0x00,
    FLOATING: 0x01,
};
export const TRANSACTION_TYPES = {
    SWAP: 0x00,
    SELL: 0x01,
    FUND: 0x02,
};
type TransactionRate = $Values<typeof TRANSACTION_RATES>;
type TransactionType = $Values<typeof TRANSACTION_TYPES>;

const maybeThrowProtocolError = (result: Buffer): void => {
    invariant(result.length >= 2, "ExchangeTransport: Unexpected result length");
    const resultCode = result.readUInt16BE(result.length - 2);
    if (resultCode !== 0x9000) {
        throw new TransportStatusError(resultCode);
    }
};

export default class Exchange {
    transport: Transport<*>;
    transactionType: TransactionType;
    transactionRate: TransactionRate;
    allowedStatuses: Array<number> = [
        RESULT.OK,
        RESULT.INCORRECT_COMMAND_DATA,
        RESULT.DESERIALIZATION_FAILED,
        RESULT.WRONG_TRANSACTION_ID,
        RESULT.INVALID_ADDRESS,
        RESULT.USER_REFUSED,
        RESULT.INTERNAL_ERROR,
        RESULT.CLASS_NOT_SUPPORTED,
        RESULT.INVALID_INSTRUCTION,
        RESULT.SIGN_VERIFICATION_FAIL,
    ];

    constructor(
        transport: Transport<*>,
        transactionType: TransactionType,
        transactionRate?: TransactionRate
    ) {
        this.transactionType = transactionType;
        this.transactionRate = transactionRate || TRANSACTION_RATES.FIXED;
        this.transport = transport;
    }

    async startNewTransaction(): Promise<string> {
        let result: Buffer = await this.transport.send(
            0xe0,
            COMMAND.START_NEW_TRANSACTION_COMMAND,
            this.transactionRate,
            this.transactionType,
            Buffer.alloc(0),
            this.allowedStatuses
        );
        maybeThrowProtocolError(result);

        if (this.transactionType === TRANSACTION_TYPES.SELL || this.transactionType === TRANSACTION_TYPES.FUND) {
            return result.subarray(0, 32).toString("base64");
        }

        return result.toString("ascii", 0, 10);
    }

    async setPartnerKey(partnerNameAndPublicKey: Buffer): Promise<void> {
        let result: Buffer = await this.transport.send(
            0xe0,
            COMMAND.SET_PARTNER_KEY_COMMAND,
            this.transactionRate,
            this.transactionType,
            partnerNameAndPublicKey,
            this.allowedStatuses
        );

        maybeThrowProtocolError(result);
    }

    async checkPartner(signatureOfPartnerData: Buffer): Promise<void> {
        let result: Buffer = await this.transport.send(
            0xe0,
            COMMAND.CHECK_PARTNER_COMMAND,
            this.transactionRate,
            this.transactionType,
            signatureOfPartnerData,
            this.allowedStatuses
        );

        maybeThrowProtocolError(result);
    }

    async processTransaction(transaction: Buffer, fee: BigNumber): Promise<void> {
        var hex: string = fee.toString(16);
        hex = hex.padStart(hex.length + (hex.length % 2), "0");
        var feeHex: Buffer = Buffer.from(hex, "hex");

        const bufferToSend: Buffer = Buffer.concat([
            Buffer.from([transaction.length]),
            transaction,
            Buffer.from([feeHex.length]),
            feeHex,
        ]);

        let result: Buffer = await this.transport.send(
            0xe0,
            COMMAND.PROCESS_TRANSACTION_RESPONSE,
            this.transactionRate,
            this.transactionType,
            bufferToSend,
            this.allowedStatuses
        );

        maybeThrowProtocolError(result);
    }

    async checkTransactionSignature(transactionSignature: Buffer): Promise<void> {
        let result: Buffer = await this.transport.send(
            0xe0,
            COMMAND.CHECK_TRANSACTION_SIGNATURE,
            this.transactionRate,
            this.transactionType,
            transactionSignature,
            this.allowedStatuses
        );
        maybeThrowProtocolError(result);
    }

    async checkPayoutAddress(
        payoutCurrencyConfig: Buffer,
        currencyConfigSignature: Buffer,
        addressParameters: Buffer
    ): Promise<void> {
        invariant(payoutCurrencyConfig.length <= 255, "Currency config is too big");
        invariant(addressParameters.length <= 255, "Address parameter is too big.");
        invariant(
            currencyConfigSignature.length >= 70 &&
            currencyConfigSignature.length <= 73,
            "Signature should be DER serialized and have length in [70, 73] bytes."
        );

        const bufferToSend: Buffer = Buffer.concat([
            Buffer.from([payoutCurrencyConfig.length]),
            payoutCurrencyConfig,
            currencyConfigSignature,
            Buffer.from([addressParameters.length]),
            addressParameters,
        ]);

        let result: Buffer = await this.transport.send(
            0xe0,
            this.transactionType === TRANSACTION_TYPES.SWAP
                ? COMMAND.CHECK_PAYOUT_ADDRESS
                : COMMAND.CHECK_ASSET_IN,
            this.transactionRate,
            this.transactionType,
            bufferToSend,
            this.allowedStatuses
        );
        maybeThrowProtocolError(result);
    }

    async checkRefundAddress(
        refundCurrencyConfig: Buffer,
        currencyConfigSignature: Buffer,
        addressParameters: Buffer
    ): Promise<void> {
        invariant(refundCurrencyConfig.length <= 255, "Currency config is too big");
        invariant(addressParameters.length <= 255, "Address parameter is too big.");
        invariant(
            currencyConfigSignature.length >= 70 &&
            currencyConfigSignature.length <= 73,
            "Signature should be DER serialized and have length in [70, 73] bytes."
        );

        const bufferToSend: Buffer = Buffer.concat([
            Buffer.from([refundCurrencyConfig.length]),
            refundCurrencyConfig,
            currencyConfigSignature,
            Buffer.from([addressParameters.length]),
            addressParameters,
        ]);

        let result: Buffer = await this.transport.send(
            0xe0,
            COMMAND.CHECK_REFUND_ADDRESS,
            this.transactionRate,
            this.transactionType,
            bufferToSend,
            this.allowedStatuses
        );
        maybeThrowProtocolError(result);
    }

    async signCoinTransaction(): Promise<void> {
        let result: Buffer = await this.transport.send(
            0xe0,
            COMMAND.SIGN_COIN_TRANSACTION,
            this.transactionRate,
            this.transactionType,
            Buffer.alloc(0),
            this.allowedStatuses
        );
        maybeThrowProtocolError(result);
    }
}
