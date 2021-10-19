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
import { TransportStatusError } from "@ledgerhq/errors";

export const TEZOS_DERIVATION_PATH = "44'/1729'/0'/0'";
export const TEZOS_PAYOUT_ADDRESS = "tz1RVYaHiobUKXMfJ47F7Rjxx5tu3LC35WSA";

export const TEZOS_DERIVATION_PATH_2 = "44'/1729'/1'/0'";
export const TEZOS_PAYOUT_ADDRESS_2 = "tz1RjJLvt7iguJQnVVWYca2AHDpHYmPJYz4d";

export const TEZOS_INVALID_PAYOUT_ADDRESS = "tz1RVYaHiobUKXMfJ47F7Rjxx5tu3LC35WSB"; // notice the B at the end

import { waitForAppScreen, zemu } from './test.fixture';

test('[Nano S] Wrong XTZ payout address should not be accepted', zemu("nanos", async (sim) => {
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
    await expect(swap.checkPayoutAddress(XTZConfig, XTZConfigSignature, params.addressParameters))
        .rejects.toEqual(new TransportStatusError(0x6a83));
}));

test('[Nano S] Valid payout address XTZ should be accepted', zemu("nanos", async (sim) => {
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
    await expect(swap.checkPayoutAddress(XTZConfig, XTZConfigSignature, params.addressParameters)).resolves.toBe(undefined);
}));

test('[Nano S] Wrong refund address should be rejected', zemu("nanos", async (sim) => {
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
}));

test('[Nano S] Valid refund address should be accepted', zemu("nanos", async (sim) => {
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

    await waitForAppScreen(sim);
    await sim.navigateAndCompareSnapshots('.', 'nanos_xtz_valid_refund_address_is_accepted', [4, 0]);

    await expect(checkRequest).resolves.toBe(undefined);
}));
