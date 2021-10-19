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
    ETHConfig, ETHConfigSignature
} from "./common";
import Exchange from "./exchange.js";
import { TransportStatusError } from "@ledgerhq/errors";

import {
    TRANSACTION_RATES,
    TRANSACTION_TYPES
} from "./exchange.js";

import { waitForAppScreen, zemu } from './test.fixture';

test('[Nano S] Wrong Ethereum payout address should not be accepted', zemu("nanos", async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("2324234324324234");
    tr.setPayinExtraId("");
    tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8e");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("ETH");
    // 1 BTC to 10 ETH
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const params = await getSerializedAddressParameters("44'/60'/0'/0/0");
    await expect(swap.checkPayoutAddress(ETHConfig, ETHConfigSignature, params.addressParameters))
        .rejects.toEqual(new TransportStatusError(0x6a83));
}));

test('[Nano S] Valid Ethereum payout address should be accepted', zemu("nanos", async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("2324234324324234");
    tr.setPayinExtraId("");
    tr.setRefundAddress("sfdsfdsfsdfdsfsdf");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("ETH");
    // 1 BTC to 10 ETH
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const params = await getSerializedAddressParameters("44'/60'/0'/0/0");
    await expect(swap.checkPayoutAddress(ETHConfig, ETHConfigSignature, params.addressParameters)).resolves.toBe(undefined);
}));

test('[Nano S] Wrong Ethereum refund address should not be accepted', zemu("nanos", async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("2324234324324234");
    tr.setPayinExtraId("");
    tr.setRefundAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8e");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("ETH");
    tr.setCurrencyTo("ETH");
    // 1 BTC to 10 ETH
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const ethAddressParams = await getSerializedAddressParameters("44'/60'/0'/0/0");
    await swap.checkPayoutAddress(ETHConfig, ETHConfigSignature, ethAddressParams.addressParameters);

    const eth2AddressParams = await getSerializedAddressParameters("44'/60'/0'/0/0");
    await expect(swap.checkRefundAddress(ETHConfig, ETHConfigSignature, eth2AddressParams.addressParameters))
        .rejects.toEqual(new TransportStatusError(0x6a83));
}));

test('[Nano S] Valid refund address should be accepted', zemu("nanos", async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
    var tr = new proto.ledger_swap.NewTransactionResponse();
    tr.setPayinAddress("2324234324324234");
    tr.setPayinExtraId("");
    tr.setRefundAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
    tr.setRefundExtraId("");
    tr.setPayoutAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("ETH");
    tr.setCurrencyTo("ETH");
    // 1 BTC to 10 ETH
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(1000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
    await swap.checkTransactionSignature(signature);
    const ethAddressParams = await getSerializedAddressParameters("44'/60'/0'/0/0");
    await swap.checkPayoutAddress(ETHConfig, ETHConfigSignature, ethAddressParams.addressParameters);

    const eth2AddressParams = await getSerializedAddressParameters("44'/60'/0'/0/0");
    const checkRequest = swap.checkRefundAddress(ETHConfig, ETHConfigSignature, eth2AddressParams.addressParameters);

    await waitForAppScreen(sim);
    await sim.navigateAndCompareSnapshots('.', 'nanos_eth_valid_refund_address_is_accepted', [4, 0]);

    await expect(checkRequest).resolves.toBe(undefined);
}));