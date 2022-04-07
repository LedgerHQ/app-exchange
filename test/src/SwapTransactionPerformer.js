import secp256k1 from "secp256k1";
import sha256 from "js-sha256";

import Exchange from "./exchange.js";
import {
    TRANSACTION_RATES,
    TRANSACTION_TYPES
} from "./exchange.js";

import { TransportStatusError } from "@ledgerhq/errors";

import Zemu from "@zondax/zemu";
import { waitForAppScreen } from './test.fixture';

import {
    numberToBigEndianBuffer,
    CurrencyInfo,
    swapTestPrivateKey,
    partnerSerializedNameAndPubKey,
    DERSignatureOfPartnerNameAndPublicKey,
    fundTestPrivateKey,
    fundPartnerSerializedNameAndPubKey,
    DERSignatureOfFundPartnerNameAndPublicKey
} from "./common";


// Helper class to factorize boilerplate transaction code
export class SwapTransactionPerformer {
    constructor(model, sim) {
        this.model = model;
        this.sim = sim;
    }

    // Which currency is FROM (use a static CurrencyInfo defined above)
    setFromCurrencyInfo(fromCurrencyInfo: CurrencyInfo) {
        this.fromCurrencyInfo = fromCurrencyInfo;
    }

    // Which currency is TO (use a static CurrencyInfo defined above)
    setToCurrencyInfo(toCurrencyInfo: CurrencyInfo) {
        this.toCurrencyInfo = toCurrencyInfo;
    }

    // What amount of FROM currency to send
    setAmountToProvider(amountToProvider: number) {
        this.amountToProvider = amountToProvider;
    }
    // What amount of TO currency to receive
    setAmountToWallet(amountToWallet: number) {
        this.amountToWallet = amountToWallet;
    }
    // The amount of FROM currency to use as fee
    setFee(fee: BigNumber) {
        this.fee = fee;
    }

    async createExchangeAndTransaction() {
        this.swap = new Exchange(this.sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await this.swap.startNewTransaction();
        await this.swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await this.swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        this.tr = new proto.ledger_swap.NewTransactionResponse();
        this.tr.setCurrencyFrom(this.fromCurrencyInfo.name);
        this.tr.setPayinAddress(this.fromCurrencyInfo.sendingAddress);
        this.tr.setPayinExtraId(this.fromCurrencyInfo.sendingExtraId);
        this.tr.setRefundAddress(this.fromCurrencyInfo.receivingAddress);
        this.tr.setRefundExtraId(this.fromCurrencyInfo.receivingExtraId);

        this.tr.setCurrencyTo(this.toCurrencyInfo.name);
        this.tr.setPayoutAddress(this.toCurrencyInfo.receivingAddress);
        this.tr.setPayoutExtraId(this.toCurrencyInfo.receivingExtraId);

        this.tr.setAmountToProvider(numberToBigEndianBuffer(this.amountToProvider));
        this.tr.setAmountToWallet(numberToBigEndianBuffer(this.amountToWallet));
        this.tr.setDeviceTransactionId(transactionId);
    }

    async processTransactionAndCheckSignature() {
        const payload: Buffer = Buffer.from(this.tr.serializeBinary());
        await this.swap.processTransaction(payload, this.fee);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await this.swap.checkTransactionSignature(signature);
    }

    async falsifyPayoutAddress() {
        this.tr.setPayoutAddress(this.toCurrencyInfo.invalidAddress);
        this.tr.setPayoutExtraId("");
    }

    async falsifyRefundAddress() {
        this.tr.setRefundAddress(this.fromCurrencyInfo.invalidAddress);
        this.tr.setRefundExtraId("");
    }

    // Perform the SWAP transaction, requires that all parameters are set
    async performInvalidPayoutTransaction() {
        await this.createExchangeAndTransaction();
        await this.falsifyPayoutAddress();
        await this.processTransactionAndCheckSignature();

        await expect(this.swap.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    }

    async performValidPayoutTransaction() {
        await this.createExchangeAndTransaction();
        await this.processTransactionAndCheckSignature();

        await expect(this.swap.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .resolves.toBe(undefined);
    }

    async performInvalidRefundTransaction() {
        await this.createExchangeAndTransaction();
        await this.falsifyRefundAddress();
        await this.processTransactionAndCheckSignature();

        await expect(this.swap.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .resolves.toBe(undefined);

        await expect(this.swap.checkRefundAddress(this.fromCurrencyInfo.config, this.fromCurrencyInfo.configSignature, this.fromCurrencyInfo.serializedAddressParameters.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    }

    async performValidPayoutValidRefundTransaction() {
        await this.createExchangeAndTransaction();
        await this.processTransactionAndCheckSignature();

        await expect(this.swap.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .resolves.toBe(undefined);

        const checkRequest = this.swap.checkRefundAddress(this.fromCurrencyInfo.config, this.fromCurrencyInfo.configSignature, this.fromCurrencyInfo.serializedAddressParameters.addressParameters);

        // Wait until we are not in the main menu
        await waitForAppScreen(this.sim);
        await this.sim.navigateAndCompareSnapshots(".", `${this.model.name}_${this.fromCurrencyInfo.displayName}_valid_refund_address_is_accepted`, [4, 0]);
        await expect(checkRequest).resolves.toBe(undefined);
    }

    // Perform the SWAP transaction, requires that all parameters are set
    async performSuccessfulTransaction() {
        await this.createExchangeAndTransaction();
        await this.processTransactionAndCheckSignature();

        await expect(this.swap.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .resolves.toBe(undefined);

        const checkRequest = this.swap.checkRefundAddress(this.fromCurrencyInfo.config, this.fromCurrencyInfo.configSignature, this.fromCurrencyInfo.serializedAddressParameters.addressParameters);

        // Wait until we are not in the main menu
        await waitForAppScreen(this.sim);
        await this.sim.navigateAndCompareSnapshots(".", `${this.model.name}_${this.fromCurrencyInfo.displayName}_to_${this.toCurrencyInfo.displayName}_swap`, [4, 0]);
        await expect(checkRequest).resolves.toBe(undefined);

        await this.swap.signCoinTransaction();

        await Zemu.sleep(500);
    }
}