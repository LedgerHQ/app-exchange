import "core-js/stable";
import "regenerator-runtime/runtime";
import secp256k1 from "secp256k1";
import sha256 from "js-sha256";
import "./protocol_pb.js";
import {
    getSerializedAddressParameters,
    numberToBigEndianBuffer,
    swapTestPrivateKey,
    partnerSerializedNameAndPubKey, DERSignatureOfPartnerNameAndPublicKey,
    XLMConfig, XLMConfigSignature
} from "./common";
import Exchange from "./exchange.js";
import {
    TRANSACTION_TYPES
} from "./exchange.js";
import { TransportStatusError } from "@ledgerhq/errors";

export const STELLAR_DERIVATION_PATH = "44'/148'/0'";
export const STELLAR_PAYOUT_ADDRESS = "GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B";

export const STELLAR_INVALID_PAYOUT_ADDRESS = "GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5C"; // notice the C at the end

import { waitForAppScreen, zemu, nano_environments } from './test.fixture';

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] XLM Wrong payout address should not be accepted`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
        tr.setRefundExtraId("");
        tr.setPayoutAddress(STELLAR_INVALID_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("BTC");
        tr.setCurrencyTo("XLM");
        // 1 BTC to 10 XLM
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const params = await getSerializedAddressParameters(STELLAR_DERIVATION_PATH);
        console.log(params);
        await expect(swap.checkPayoutAddress(XLMConfig, XLMConfigSignature, params.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    }))
});


nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] XLM Valid payout address should be accepted`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
        tr.setRefundExtraId("");
        tr.setPayoutAddress(STELLAR_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("BTC");
        tr.setCurrencyTo("XLM");
        // 1 BTC to 10 XLM
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const params = await getSerializedAddressParameters(STELLAR_DERIVATION_PATH);
        console.log(params);
        await expect(swap.checkPayoutAddress(XLMConfig, XLMConfigSignature, params.addressParameters)).resolves.toBe(undefined);
    }))
});


nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] XLM Wrong refund address should be rejected`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress(STELLAR_INVALID_PAYOUT_ADDRESS);
        tr.setRefundExtraId("");
        tr.setPayoutAddress(STELLAR_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("XLM");
        tr.setCurrencyTo("XLM");
        // 1 XLM to 10 XLM
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const xlmAddressParams = await getSerializedAddressParameters(STELLAR_DERIVATION_PATH);
        await swap.checkPayoutAddress(XLMConfig, XLMConfigSignature, xlmAddressParams.addressParameters);

        const xlm2AddressParams = await getSerializedAddressParameters(STELLAR_DERIVATION_PATH);
        await expect(swap.checkRefundAddress(XLMConfig, XLMConfigSignature, xlm2AddressParams.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    }))
});


nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] XLM Valid refund address should be accepted`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress(STELLAR_PAYOUT_ADDRESS);
        tr.setRefundExtraId("");
        tr.setPayoutAddress(STELLAR_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("XLM");
        tr.setCurrencyTo("XLM");
        // 1 XLM to 10 XLM
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const xlmAddressParams = await getSerializedAddressParameters(STELLAR_DERIVATION_PATH);
        await swap.checkPayoutAddress(XLMConfig, XLMConfigSignature, xlmAddressParams.addressParameters);

        const xlm2AddressParams = await getSerializedAddressParameters(STELLAR_DERIVATION_PATH);
        const checkRequest = swap.checkRefundAddress(XLMConfig, XLMConfigSignature, xlm2AddressParams.addressParameters);

        await waitForAppScreen(sim);
        await sim.navigateAndCompareSnapshots('.', `${model.name}_xlm_valid_refund_address_is_accepted`, [4, 0]);

        await expect(checkRequest).resolves.toBe(undefined);
    }))
});

