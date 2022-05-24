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
    XRPConfig, XRPConfigSignature
} from "./common";
import Exchange from "./exchange.js";
import {
    TRANSACTION_TYPES
} from "./exchange.js";
import { TransportStatusError } from "@ledgerhq/errors";

export const XRP_DERIVATION_PATH = "44'/144'/0'/0/0";
export const XRP_PAYOUT_ADDRESS = "ra7Zr8ddy9tB88RaXL8B87YkqhEJG2vkAJ";

export const XRP_DERIVATION_PATH_2 = "44'/144'/0'/1/0";
export const XRP_PAYOUT_ADDRESS_2 = "rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4";

export const XRP_INVALID_PAYOUT_ADDRESS = "Ka7Zr8ddy9tB88RaXL8B87YkqhEJG2vkAK";

import { waitForAppScreen, zemu, nano_environments } from './test.fixture';

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] XRP Wrong payout address should not be accepted`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
        tr.setRefundExtraId("");
        tr.setPayoutAddress(XRP_INVALID_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("BTC");
        tr.setCurrencyTo("XRP");
        // 1 BTC to 10 XRP
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const params = await getSerializedAddressParameters(XRP_DERIVATION_PATH);
        await expect(swap.checkPayoutAddress(XRPConfig, XRPConfigSignature, params.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] XRP Valid payout address should be accepted`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
        tr.setRefundExtraId("");
        tr.setPayoutAddress(XRP_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("BTC");
        tr.setCurrencyTo("XRP");
        // 1 BTC to 10 XRP
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const params = await getSerializedAddressParameters(XRP_DERIVATION_PATH);
        await expect(swap.checkPayoutAddress(XRPConfig, XRPConfigSignature, params.addressParameters)).resolves.toBe(undefined);
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] XRP Wrong refund address should be rejected`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress(XRP_INVALID_PAYOUT_ADDRESS);
        tr.setRefundExtraId("");
        tr.setPayoutAddress(XRP_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("XRP");
        tr.setCurrencyTo("XRP");
        // 1 XRP to 10 XRP
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const xrpAddressParams = await getSerializedAddressParameters(XRP_DERIVATION_PATH);
        await swap.checkPayoutAddress(XRPConfig, XRPConfigSignature, xrpAddressParams.addressParameters);

        const xrp2AddressParams = await getSerializedAddressParameters(XRP_DERIVATION_PATH_2);
        await expect(swap.checkRefundAddress(XRPConfig, XRPConfigSignature, xrp2AddressParams.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] XRP Valid refund address should be accepted`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress(XRP_PAYOUT_ADDRESS_2);
        tr.setRefundExtraId("");
        tr.setPayoutAddress(XRP_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("XRP");
        tr.setCurrencyTo("XRP");
        // 1 XRP to 10 XRP
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const xrpAddressParams = await getSerializedAddressParameters(XRP_DERIVATION_PATH);
        await swap.checkPayoutAddress(XRPConfig, XRPConfigSignature, xrpAddressParams.addressParameters);

        const xrp2AddressParams = await getSerializedAddressParameters(XRP_DERIVATION_PATH_2);
        const checkRequest = swap.checkRefundAddress(XRPConfig, XRPConfigSignature, xrp2AddressParams.addressParameters);

        await waitForAppScreen(sim);
        await sim.navigateAndCompareSnapshots('.', `${model.name}_xrp_valid_refund_address_is_accepted`, [4, 0]);

        await expect(checkRequest).resolves.toBe(undefined);
    }))
});
