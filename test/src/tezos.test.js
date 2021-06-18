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
    XTZConfig, XTZConfigSignature
} from "./common"; import Exchange from "./exchange.js";
import Zemu from "@zondax/zemu";
import { TransportStatusError } from "@ledgerhq/errors";

const sim_options = {
    logging: true,
    start_delay: 1500,
    X11: true
};
const Resolve = require("path").resolve;
const APP_PATH = Resolve("elfs/exchange.elf");
const XTZ_LIB = { "\"Tezos Wallet\"": Resolve("elfs/tezos.elf") };

export const TEZOS_DERIVATION_PATH = "44'/1729'/0'/0'";
export const TEZOS_PAYOUT_ADDRESS = "tz1RVYaHiobUKXMfJ47F7Rjxx5tu3LC35WSA";

export const TEZOS_DERIVATION_PATH_2 = "44'/1729'/1'/0'";
export const TEZOS_PAYOUT_ADDRESS_2 = "tz1RjJLvt7iguJQnVVWYca2AHDpHYmPJYz4d";

export const TEZOS_INVALID_PAYOUT_ADDRESS = "tz1RVYaHiobUKXMfJ47F7Rjxx5tu3LC35WSB"; // notice the B at the end

test('Wrong payout address XTZ should not be accepted', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, XTZ_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), 0x00);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress(TEZOS_INVALID_PAYOUT_ADDRESS);
        tr.setRefundExtraId("");
        tr.setPayoutAddress(TEZOS_INVALID_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("BTC");
        tr.setCurrencyTo("XTZ");
        // 1 BTC to 10 XTZ
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const params = await getSerializedAddressParameters(TEZOS_DERIVATION_PATH);
        console.log(params);
        await expect(swap.checkPayoutAddress(XTZConfig, XTZConfigSignature, params.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    } finally {
        await sim.close();
    }
})

test('Valid payout address XTZ should be accepted', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, XTZ_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), 0x00);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress(TEZOS_INVALID_PAYOUT_ADDRESS);
        tr.setRefundExtraId("");
        tr.setPayoutAddress(TEZOS_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("BTC");
        tr.setCurrencyTo("XTZ");
        // 1 BTC to 10 XTZ
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const params = await getSerializedAddressParameters(TEZOS_DERIVATION_PATH);
        console.log(params);
        await expect(swap.checkPayoutAddress(XTZConfig, XTZConfigSignature, params.addressParameters)).resolves.toBe(undefined);
    } finally {
        await sim.close();
    }
})

test('Wrong refund address should be rejected', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, XTZ_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), 0x00);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress(TEZOS_INVALID_PAYOUT_ADDRESS);
        tr.setRefundExtraId("");
        tr.setPayoutAddress(TEZOS_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("XTZ");
        tr.setCurrencyTo("XTZ");
        // 1 BTC to 10 XTZ
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const xtzAddressParams = await getSerializedAddressParameters(TEZOS_DERIVATION_PATH);
        await swap.checkPayoutAddress(XTZConfig, XTZConfigSignature, xtzAddressParams.addressParameters);

        const xtz2AddressParams = await getSerializedAddressParameters(TEZOS_DERIVATION_PATH);
        await expect(swap.checkRefundAddress(XTZConfig, XTZConfigSignature, xtz2AddressParams.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    } finally {
        await sim.close();
    }
})

test('Valid refund address should be accepted', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, XTZ_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), 0x00);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress(TEZOS_PAYOUT_ADDRESS_2);
        tr.setRefundExtraId("");
        tr.setPayoutAddress(TEZOS_PAYOUT_ADDRESS);
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("XTZ");
        tr.setCurrencyTo("XTZ");
        // 1 BTC to 10 XTZ
        tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 10000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const xtzAddressParams = await getSerializedAddressParameters(TEZOS_DERIVATION_PATH);
        await swap.checkPayoutAddress(XTZConfig, XTZConfigSignature, xtzAddressParams.addressParameters);

        const xtz2AddressParams = await getSerializedAddressParameters(TEZOS_DERIVATION_PATH_2);
        const checkRequest = swap.checkRefundAddress(XTZConfig, XTZConfigSignature, xtz2AddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());

        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickBoth();

        await expect(checkRequest).resolves.toBe(undefined);
    } finally {
        await sim.close();
    }
})
