import "core-js/stable";
import "regenerator-runtime/runtime";
import Btc from "@ledgerhq/hw-app-btc";
import secp256k1 from "secp256k1";
import sha256 from "js-sha256";
import "./protocol_pb.js";
import {
    getSerializedAddressParametersBTC,
    numberToBigEndianBuffer,
    swapTestPrivateKey,
    partnerSerializedNameAndPubKey, DERSignatureOfPartnerNameAndPublicKey,
    BTCConfig, BTCConfigSignature,
    LTCConfig, LTCConfigSignature,
} from "./common";
import Exchange from "./exchange.js";
import {
    TRANSACTION_TYPES
} from "./exchange.js";
import Zemu from "@zondax/zemu";
import { TransportStatusError } from "@ledgerhq/errors";

import { waitForAppScreen, zemu, nano_environments } from './test.fixture';

test('[Nano S] Wrong payout address should be rejected', zemu(nano_environments[0], async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("2324234324324234");
    tr.setPayinExtraId("");
    tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("LKtSt6xfsmJMkPT8YyViAsDeRh7k8UfNjL");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("LTC");
    // 1 BTC to 1 LTC
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(48430000000000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const params = await getSerializedAddressParametersBTC("49'/0'/0'/0/0");
    console.log(params);
    await expect(swap.checkPayoutAddress(LTCConfig, LTCConfigSignature, params.addressParameters))
        .rejects.toEqual(new TransportStatusError(0x6a83));
}));

test('[Nano S] Valid Bitcoin payout address should be accepted', zemu(nano_environments[0], async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("2324234324324234");
    tr.setPayinExtraId("");
    tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("LKtSt6xfsmJMkPT8YyViAsDeRh7k8UfNjD");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("LTC");
    // 1 BTC to 10 LTC
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const params = await getSerializedAddressParametersBTC("49'/0'/0'/0/0");
    console.log(params);
    await expect(swap.checkPayoutAddress(LTCConfig, LTCConfigSignature, params.addressParameters)).resolves.toBe(undefined);
}));

test('[Nano S] Wrong Bitcoin refund address should not be accepted', zemu(nano_environments[0], async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("2324234324324234");
    tr.setPayinExtraId("");
    tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("LKtSt6xfsmJMkPT8YyViAsDeRh7k8UfNjD");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("LTC");
    // 1 BTC to 10 LTC
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const ltcAddressParams = await getSerializedAddressParametersBTC("49'/0'/0'/0/0");
    await swap.checkPayoutAddress(LTCConfig, LTCConfigSignature, ltcAddressParams.addressParameters);

    const btcAddressParams = await getSerializedAddressParametersBTC("84'/0'/0'/1/0", "bech32");
    await expect(swap.checkRefundAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters))
        .rejects.toEqual(new TransportStatusError(0x6a83));
}));

test('[Nano S] Valid refund address should be accepted', zemu(nano_environments[0], async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("2324234324324234");
    tr.setPayinExtraId("");
    tr.setRefundAddress("bc1qwpgezdcy7g6khsald7cww42lva5g5dmasn6y2z");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("LKtSt6xfsmJMkPT8YyViAsDeRh7k8UfNjD");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("LTC");
    // 1 BTC to 10 LTC
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const ltcAddressParams = await getSerializedAddressParametersBTC("49'/0'/0'/0/0");
    await swap.checkPayoutAddress(LTCConfig, LTCConfigSignature, ltcAddressParams.addressParameters);

    const btcAddressParams = await getSerializedAddressParametersBTC("84'/0'/0'/1/0", "bech32");
    const checkRequest = swap.checkRefundAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);

    // Wait until we are not in the main menu
    await waitForAppScreen(sim);
    await sim.navigateAndCompareSnapshots('.', 'nanos_btc_valid_refund_address_is_accepted', [4, 0]);

    await expect(checkRequest).resolves.toBe(undefined);
}));

// tests with taproot addresses

test('[Nano S] Valid taproot refund address should be accepted', zemu(nano_environments[0], async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("2324234324324234");
    tr.setPayinExtraId("");
    tr.setRefundAddress("bc1p3a2hvrnu9pddga5umef49keepgcw7yvz5a7m2uxx6vsrmth4p40qzrgjwr");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("LKtSt6xfsmJMkPT8YyViAsDeRh7k8UfNjD");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("LTC");
    // 1 BTC to 10 LTC
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const ltcAddressParams = await getSerializedAddressParametersBTC("49'/0'/0'/0/0");
    await swap.checkPayoutAddress(LTCConfig, LTCConfigSignature, ltcAddressParams.addressParameters);

    const btcAddressParams = await getSerializedAddressParametersBTC("86'/0'/0'/0/6", "bech32m");
    const checkRequest = swap.checkRefundAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);

    // Wait until we are not in the main menu
    await waitForAppScreen(sim);
    await sim.navigateAndCompareSnapshots('.', 'nanos_btc_valid_taproot_refund_address_is_accepted', [4, 0]);

    await expect(checkRequest).resolves.toBe(undefined);
}));

// Forcing AmountToWallet to be bigger than 8B, so that the Bitcoin app would
// accept it only if the trim function works as expected
test('[Nano S] Overflow values should be trimmed when swapping', zemu(nano_environments[0], async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("0xd692Cb1346262F584D17B4B470954501f6715a82");
    tr.setPayinExtraId("");
    tr.setRefundAddress("bc1qwpgezdcy7g6khsald7cww42lva5g5dmasn6y2z");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("bc1qwpgezdcy7g6khsald7cww42lva5g5dmasn6y2z");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("BTC");
    tr.setAmountToProvider(Buffer.from(['0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x10', '0x10', '0x10', '0x10']));
    tr.setAmountToWallet(Buffer.from(['0x00', '0x00', '0x00', '0x00', '0x00', '0x05', '0xf5', '0xe1', '0x00']));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 840000000000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const btcAddressParams = getSerializedAddressParametersBTC("84'/0'/0'/1/0", "bech32");
    await swap.checkPayoutAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);

    const checkRequest = swap.checkRefundAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);

    // Wait until we are not in the main menu
    await waitForAppScreen(sim);
    await sim.navigateAndCompareSnapshots('.', 'nanos_btc_to_btc_overload_swap', [4, 0]);
    await expect(checkRequest).resolves.toBe(undefined);
}));
