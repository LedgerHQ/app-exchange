import secp256k1 from "secp256k1";
import secp256r1 from "secp256r1";
import sha256 from "js-sha256";
import base64url from "base64url";

import Exchange from "./exchange.js";
import { TRANSACTION_TYPES } from "./exchange.js";
import { RESULT } from "Swap.js";

import { TransportStatusError } from "@ledgerhq/errors";

import Zemu from "@zondax/zemu";
import { waitForAppScreen } from './test.fixture';

import {
    numberToBigEndianBuffer,
    CurrencyInfo,
    swapTestPrivateKey,
    sellTestPrivateKey,
    fundTestPrivateKey,
    partnerSerializedNameAndPubKey,
    DERSignatureOfPartnerNameAndPublicKey,
    sellPartnerSerializedNameAndPubKey,
    DERSignatureOfSellPartnerNameAndPublicKey,
    fundPartnerSerializedNameAndPubKey,
    DERSignatureOfFundPartnerNameAndPublicKey,
} from "./common";


// Helper class to factorize boilerplate transaction code
export class SwapTransactionPerformer {
    constructor(model, sim) {
        this.model = model;
        this.sim = sim;
    }

    // COMMON
    // Which currency is FROM (use a static CurrencyInfo defined above)
    setFromCurrencyInfo(fromCurrencyInfo: CurrencyInfo) {
        this.fromCurrencyInfo = fromCurrencyInfo;
    }
    // Which currency is TO (use a static CurrencyInfo defined above)
    setToCurrencyInfo(toCurrencyInfo: CurrencyInfo) {
        this.toCurrencyInfo = toCurrencyInfo;
    }
    // The amount of FROM currency to use as fee
    setFee(fee: BigNumber) {
        this.fee = fee;
    }

    // SWAP
    // What amount of FROM currency to send
    setAmountToProvider(amountToProvider: number) {
        this.amountToProvider = numberToBigEndianBuffer(amountToProvider);
    }
    // SWAP
    // What amount of TO currency to receive
    setAmountToWallet(amountToWallet: number) {
        this.amountToWallet = numberToBigEndianBuffer(amountToWallet);
    }

    // SELL + FUND
    // What amount of FROM currency to send
    setInAmount(inAmount) {
        this.inAmount = inAmount;
    }
    // SELL
    // What amount of TO currency to receive
    setOutAmount(coefficient: number, exponent: number) {
        const outAmount = new proto.ledger_swap.UDecimal();
        outAmount.setCoefficient(new Uint8Array(numberToBigEndianBuffer(coefficient)));
        outAmount.setExponent(exponent);
        this.outAmount = outAmount;
    }

    async createSwapTransaction(falsifyPayoutAddress: boolean, falsifyRefundAddress: boolean) {
        this.exchange = new Exchange(this.sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await this.exchange.startNewTransaction();
        await this.exchange.setPartnerKey(partnerSerializedNameAndPubKey);
        await this.exchange.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        this.tr = new proto.ledger_swap.NewTransactionResponse();
        this.tr.setCurrencyFrom(this.fromCurrencyInfo.name);
        this.tr.setPayinAddress(this.fromCurrencyInfo.sendingAddress);
        this.tr.setPayinExtraId(this.fromCurrencyInfo.sendingExtraId);
        if (falsifyRefundAddress) {
            this.tr.setRefundAddress(this.fromCurrencyInfo.invalidAddress);
            this.tr.setRefundExtraId("");
        } else {
            this.tr.setRefundAddress(this.fromCurrencyInfo.receivingAddress);
            this.tr.setRefundExtraId(this.fromCurrencyInfo.receivingExtraId);
        }

        this.tr.setCurrencyTo(this.toCurrencyInfo.name);
        if (falsifyPayoutAddress) {
            this.tr.setPayoutAddress(this.toCurrencyInfo.invalidAddress);
            this.tr.setPayoutExtraId("");
        } else {
            this.tr.setPayoutAddress(this.toCurrencyInfo.receivingAddress);
            this.tr.setPayoutExtraId(this.toCurrencyInfo.receivingExtraId);
        }

        this.tr.setAmountToProvider(this.amountToProvider);
        this.tr.setAmountToWallet(this.amountToWallet);
        this.tr.setDeviceTransactionId(transactionId);
    }

    async createSellTransaction() {
        this.exchange = new Exchange(this.sim.getTransport(), TRANSACTION_TYPES.SELL);
        const transactionId_base64: string = await this.exchange.startNewTransaction();
        const transactionId: Buffer = base64url.toBuffer(transactionId_base64);
        await this.exchange.setPartnerKey(sellPartnerSerializedNameAndPubKey);
        await this.exchange.checkPartner(DERSignatureOfSellPartnerNameAndPublicKey);
        this.tr = new proto.ledger_swap.NewSellResponse();
        this.tr.setTraderEmail("trader@email.com");
        this.tr.setInCurrency(this.fromCurrencyInfo.name);
        this.tr.setInAddress(this.fromCurrencyInfo.sendingAddress);

        this.tr.setOutCurrency(this.toCurrencyInfo.name);

        this.tr.setInAmount(this.inAmount);
        this.tr.setOutAmount(this.outAmount);
        this.tr.setDeviceTransactionId(transactionId);
    }

    async createFundTransaction() {
        this.exchange = new Exchange(this.sim.getTransport(), TRANSACTION_TYPES.FUND);
        const transactionId_base64: string = await this.exchange.startNewTransaction();
        const transactionId: Buffer = base64url.toBuffer(transactionId_base64);
        await this.exchange.setPartnerKey(fundPartnerSerializedNameAndPubKey);
        await this.exchange.checkPartner(DERSignatureOfFundPartnerNameAndPublicKey);
        this.tr = new proto.ledger_swap.NewFundResponse();
        this.tr.setUserId("John Doe");
        this.tr.setAccountName("Card 1234");
        this.tr.setInCurrency(this.fromCurrencyInfo.name);
        this.tr.setInAddress(this.fromCurrencyInfo.sendingAddress);
        this.tr.setInAmount(this.inAmount);
        this.tr.setDeviceTransactionId(transactionId);
    }

    async processTransactionAndCheckSignature(curve, concatenateDot: boolean, doEncode: boolean, privateKey) {
        let payload: Buffer = Buffer.from(this.tr.serializeBinary());
        let digest: Buffer;
        if (concatenateDot) {
            payload = Buffer.from(base64url(payload));
            digest = Buffer.from(sha256.sha256.array(Buffer.concat([Buffer.from('.'), payload])));
        } else {
            digest = Buffer.from(sha256.sha256.array(payload));
        }
        await this.exchange.processTransaction(payload, this.fee);
        const sigObj = curve.sign(digest, privateKey).signature;
        if (doEncode) {
            await this.exchange.checkTransactionSignature(curve.signatureExport(sigObj));
        } else {
            await this.exchange.checkTransactionSignature(sigObj);
        }
    }

    // Perform the SWAP transaction, requires that all parameters are set
    async performInvalidPayoutTransaction() {
        await this.createSwapTransaction(true, false);
        await this.processTransactionAndCheckSignature(secp256k1, false, true, swapTestPrivateKey);

        await expect(this.exchange.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .rejects.toEqual(new TransportStatusError(RESULT.INVALID_ADDRESS));
    }

    async performValidPayoutTransaction() {
        await this.createSwapTransaction(false, false);
        await this.processTransactionAndCheckSignature(secp256k1, false, true, swapTestPrivateKey);

        await expect(this.exchange.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .resolves.toBe(undefined);
    }

    async performInvalidRefundTransaction() {
        await this.createSwapTransaction(false, true);
        await this.processTransactionAndCheckSignature(secp256k1, false, true, swapTestPrivateKey);

        await expect(this.exchange.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .resolves.toBe(undefined);

        await expect(this.exchange.checkRefundAddress(this.fromCurrencyInfo.config, this.fromCurrencyInfo.configSignature, this.fromCurrencyInfo.serializedAddressParameters.addressParameters))
            .rejects.toEqual(new TransportStatusError(RESULT.INVALID_ADDRESS));
    }

    async performValidPayoutValidRefundTransaction() {
        await this.createSwapTransaction(false, false);
        await this.processTransactionAndCheckSignature(secp256k1, false, true, swapTestPrivateKey);

        await expect(this.exchange.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .resolves.toBe(undefined);

        const checkRequest = this.exchange.checkRefundAddress(this.fromCurrencyInfo.config, this.fromCurrencyInfo.configSignature, this.fromCurrencyInfo.serializedAddressParameters.addressParameters);

        // Wait until we are not in the main menu
        await waitForAppScreen(this.sim);
        await this.sim.navigateAndCompareSnapshots(".", `${this.model.name}_${this.fromCurrencyInfo.displayName}_valid_refund_address_is_accepted`, [4, 0]);
        await expect(checkRequest).resolves.toBe(undefined);
    }

    // Perform the SWAP transaction, requires that all parameters are set
    async performSuccessfulTransaction() {
        await this.createSwapTransaction(false, false);
        await this.processTransactionAndCheckSignature(secp256k1, false, true, swapTestPrivateKey);

        await expect(this.exchange.checkPayoutAddress(this.toCurrencyInfo.config, this.toCurrencyInfo.configSignature, this.toCurrencyInfo.serializedAddressParameters.addressParameters))
            .resolves.toBe(undefined);

        const checkRequest = this.exchange.checkRefundAddress(this.fromCurrencyInfo.config, this.fromCurrencyInfo.configSignature, this.fromCurrencyInfo.serializedAddressParameters.addressParameters);

        // Wait until we are not in the main menu
        await waitForAppScreen(this.sim);
        await this.sim.navigateAndCompareSnapshots(".", `${this.model.name}_${this.fromCurrencyInfo.displayName}_to_${this.toCurrencyInfo.displayName}_swap`, [4, 0]);
        await expect(checkRequest).resolves.toBe(undefined);

        await this.exchange.signCoinTransaction();

        await Zemu.sleep(500);
    }

    // Perform the SELL transaction, requires that all parameters are set
    async performSell() {
        await this.createSellTransaction();
        await this.processTransactionAndCheckSignature(secp256r1, true, false, sellTestPrivateKey);

        // // useless what to put instead?
        this.exchange.checkPayoutAddress(this.fromCurrencyInfo.config, this.fromCurrencyInfo.configSignature, this.fromCurrencyInfo.serializedAddressParameters.addressParameters);

        // Wait until we are not in the main menu
        await waitForAppScreen(this.sim);
        await this.sim.navigateAndCompareSnapshots('.', `${this.model.name}_valid_${this.fromCurrencyInfo.displayName}_selling_is_accepted`, [5, 0]);

        await this.exchange.signCoinTransaction();
    }

    // Perform the FUND transaction, requires that all parameters are set
    async performFund() {
        await this.createFundTransaction();
        await this.processTransactionAndCheckSignature(secp256r1, true, true, fundTestPrivateKey);

        // // useless what to put instead?
        this.exchange.checkPayoutAddress(this.fromCurrencyInfo.config, this.fromCurrencyInfo.configSignature, this.fromCurrencyInfo.serializedAddressParameters.addressParameters);

        // Wait until we are not in the main menu
        await waitForAppScreen(this.sim);
        await this.sim.navigateAndCompareSnapshots('.', `${this.model.name}_valid_${this.fromCurrencyInfo.displayName}_funding_is_accepted`, [5, 0]);

        await this.exchange.signCoinTransaction();
    }
}
