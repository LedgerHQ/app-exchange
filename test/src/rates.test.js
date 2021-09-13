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
const XRP_LIB = { "XRP": Resolve("elfs/xrp.elf") };
jest.setTimeout(50000);

test('Compare fixed rate screenshot', async () => {
    const sim = new Zemu(APP_PATH, XRP_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("ra7Zr8ddy9tB88RaXL8B87YkqhEJG2vkAJ");
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
        const xrpAddressParams = await getSerializedAddressParameters("44'/144'/0'/0/0");
        await swap.checkPayoutAddress(XRPConfig, XRPConfigSignature, xrpAddressParams.addressParameters);

        const xrp2AddressParams = await getSerializedAddressParameters("44'/144'/0'/1/0");
        const checkRequest = swap.checkRefundAddress(XRPConfig, XRPConfigSignature, xrp2AddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());

        // Capture screenshots
        await sim.clickRight("snapshots/tmp/send.png"); // Send screen
        const send = Zemu.LoadPng2RGB("snapshots/tmp/send.png");
        await sim.clickRight("snapshots/tmp/get.png"); // Get screen
        const get = Zemu.LoadPng2RGB("snapshots/tmp/get.png");
        await sim.clickRight("snapshots/tmp/fees.png"); // Fees screen
        const fees = Zemu.LoadPng2RGB("snapshots/tmp/fees.png");
        await sim.clickRight("snapshots/tmp/accept.png"); // Accept screen
        const accept = Zemu.LoadPng2RGB("snapshots/tmp/accept.png");
        await sim.clickBoth();

        // Load the expected results of the screenshots
        const expected_send = Zemu.LoadPng2RGB("snapshots/fixed_rate/send.png");
        const expected_get = Zemu.LoadPng2RGB("snapshots/fixed_rate/get.png");
        const expected_fees = Zemu.LoadPng2RGB("snapshots/fixed_rate/fees.png");
        const expected_accept = Zemu.LoadPng2RGB("snapshots/fixed_rate/accept.png");

        // Compare expected results with actual data
        expect(expected_send).toEqual(send);
        expect(expected_get).toEqual(get);
        expect(expected_fees).toEqual(fees);
        expect(expected_accept).toEqual(accept);

        await expect(checkRequest).resolves.toBe(undefined);
    } finally {
        await sim.close();
    }
})

test('Compare floating rate screenshot', async () => {
    const sim = new Zemu(APP_PATH, XRP_LIB);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP, TRANSACTION_RATES.FLOATING);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("2324234324324234");
        tr.setPayinExtraId("");
        tr.setRefundAddress("rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("ra7Zr8ddy9tB88RaXL8B87YkqhEJG2vkAJ");
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
        const xrpAddressParams = await getSerializedAddressParameters("44'/144'/0'/0/0");
        await swap.checkPayoutAddress(XRPConfig, XRPConfigSignature, xrpAddressParams.addressParameters);

        const xrp2AddressParams = await getSerializedAddressParameters("44'/144'/0'/1/0");
        const checkRequest = swap.checkRefundAddress(XRPConfig, XRPConfigSignature, xrp2AddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());

        // Capture screenshots
        await sim.clickRight("snapshots/tmp/send.png"); // Send screen
        const send = Zemu.LoadPng2RGB("snapshots/tmp/send.png");
        await sim.clickRight("snapshots/tmp/get.png"); // Get screen
        const get = Zemu.LoadPng2RGB("snapshots/tmp/get.png");
        await sim.clickRight("snapshots/tmp/fees.png"); // Fees screen
        const fees = Zemu.LoadPng2RGB("snapshots/tmp/fees.png");
        await sim.clickRight("snapshots/tmp/accept.png"); // Accept screen
        const accept = Zemu.LoadPng2RGB("snapshots/tmp/accept.png");
        await sim.clickBoth();

        // Load the expected results of the screenshots
        const expected_send = Zemu.LoadPng2RGB("snapshots/floating_rate/send.png");
        const expected_get = Zemu.LoadPng2RGB("snapshots/floating_rate/get.png");
        const expected_fees = Zemu.LoadPng2RGB("snapshots/floating_rate/fees.png");
        const expected_accept = Zemu.LoadPng2RGB("snapshots/floating_rate/accept.png");

        // Compare expected results with actual data
        expect(expected_send).toEqual(send);
        expect(expected_get).toEqual(get);
        expect(expected_fees).toEqual(fees);
        expect(expected_accept).toEqual(accept);

        await expect(checkRequest).resolves.toBe(undefined);
    } finally {
        await sim.close();
    }
})