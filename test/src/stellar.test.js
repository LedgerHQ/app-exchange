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
    TRANSACTION_RATES,
    TRANSACTION_TYPES
} from "./exchange.js";
import Zemu from "@zondax/zemu";
import { TransportStatusError } from "@ledgerhq/errors";

const sim_options = {
    logging: true,
    start_delay: 1500,
    X11: true,
    model: "nanos",
};
const Resolve = require("path").resolve;
const APP_PATH = Resolve("elfs/exchange.elf");
const XLM_LIB = { "Stellar": Resolve("elfs/stellar.elf") };
jest.setTimeout(50000);

test('Wrong payout address XLM should not be accepted', async () => {
    const sim = new Zemu(APP_PATH, XLM_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5C");
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
        const params = await getSerializedAddressParameters("44'/148'/0'");
        console.log(params);
        await expect(swap.checkPayoutAddress(XLMConfig, XLMConfigSignature, params.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    } finally {
        await sim.close();
    }
})

test('Valid payout address XLM should be accepted', async () => {
    const sim = new Zemu(APP_PATH, XLM_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B");
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
        const params = await getSerializedAddressParameters("44'/148'/0'");
        console.log(params);
        await expect(swap.checkPayoutAddress(XLMConfig, XLMConfigSignature, params.addressParameters)).resolves.toBe(undefined);
    } finally {
        await sim.close();
    }
})



test('Wrong refund address should be rejected', async () => {
    const sim = new Zemu(APP_PATH, XLM_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5C");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B");
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
        const xlmAddressParams = await getSerializedAddressParameters("44'/148'/0'");
        await swap.checkPayoutAddress(XLMConfig, XLMConfigSignature, xlmAddressParams.addressParameters);

        const xlm2AddressParams = await getSerializedAddressParameters("44'/148'/0'");
        await expect(swap.checkRefundAddress(XLMConfig, XLMConfigSignature, xlm2AddressParams.addressParameters))
            .rejects.toEqual(new TransportStatusError(0x6a83));
    } finally {
        await sim.close();
    }
})

test('Valid refund address should be accepted', async () => {
    const sim = new Zemu(APP_PATH, XLM_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B");
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
        const xlmAddressParams = await getSerializedAddressParameters("44'/148'/0'");
        await swap.checkPayoutAddress(XLMConfig, XLMConfigSignature, xlmAddressParams.addressParameters);

        const xlm2AddressParams = await getSerializedAddressParameters("44'/148'/0'");
        const checkRequest = swap.checkRefundAddress(XLMConfig, XLMConfigSignature, xlm2AddressParams.addressParameters);
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