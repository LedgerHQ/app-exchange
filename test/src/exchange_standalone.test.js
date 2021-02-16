// @flow
import "core-js/stable";
import "regenerator-runtime/runtime";

import Exchange from "./exchange.js";
import {
  TRANSACTION_RATES,
  TRANSACTION_TYPES
} from "./exchange.js";
import secp256k1 from "secp256k1";
import sha256 from "js-sha256";
import "./protocol_pb.js";
import { TransportStatusError } from "@ledgerhq/errors";
import {
  numberToBigEndianBuffer,
  swapTestPrivateKey,
  partnerSerializedNameAndPubKey, DERSignatureOfPartnerNameAndPublicKey,
} from "./common"; import Zemu from "@zondax/zemu";

const sim_options = {
  logging: true,
  start_delay: 1500,
};
const Resolve = require("path").resolve;
const APP_PATH = Resolve("../bin/app.elf");

test('can start and stop container', async function () {
  const sim = new Zemu(APP_PATH);
  try {
    await sim.start(sim_options);
  } finally {
    await sim.close();
  }
});

test('TransactionId should be 10 uppercase letters', async () => {
  const sim = new Zemu(APP_PATH);
  try {
    await sim.start(sim_options);
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    expect(transactionId.length).toBe(10);
    expect(transactionId).toBe(transactionId.toUpperCase());
  } finally {
    await sim.close();
  }
})

test('SetPartnerKey should not throw', async () => {
  const sim = new Zemu(APP_PATH);
  try {
    await sim.start(sim_options);
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await expect(swap.setPartnerKey(partnerSerializedNameAndPubKey)).resolves.toBe(undefined);
  } finally {
    await sim.close();
  }
})

test('Wrong partner data signature should not be accepted', async () => {
  const sim = new Zemu(APP_PATH);
  try {
    await sim.start(sim_options);
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await expect(swap.checkPartner(Buffer.alloc(70)))
      .rejects.toEqual(new TransportStatusError(0x9d1a));
  } finally {
    await sim.close();
  }
})

test('Correct signature of partner data should be accepted', async () => {
  const sim = new Zemu(APP_PATH);
  try {
    await sim.start(sim_options);
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
    const transactionId: string = await swap.startNewTransaction();
    await swap.setPartnerKey(partnerSerializedNameAndPubKey);
    await expect(swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey)).resolves.toBe(undefined);
  } finally {
    await sim.close();
  }
})


test('Process transaction should not fail', async () => {
  const sim = new Zemu(APP_PATH);
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
    tr.setPayoutAddress("asdasdassasadsada");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("ETH");
    // 100000000 Satoshi to 48430000000000000000 Wei (1 BTC to 48.43 ETH)
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(48430000000000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await expect(swap.processTransaction(payload, 10000000)).resolves.toBe(undefined);
  } finally {
    await sim.close();
  }
})

test('Transaction signature should be checked without errors', async () => {
  const sim = new Zemu(APP_PATH);
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
    tr.setPayoutAddress("asdasdassasadsada");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("ETH");
    // 100000000 Satoshi to 48430000000000000000 Wei (1 BTC to 48.43 ETH)
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(48430000000000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.sign(digest, swapTestPrivateKey).signature;
    await expect(swap.checkTransactionSignature(secp256k1.signatureExport(signature))).resolves.toBe(undefined);
  } finally {
    await sim.close();
  }
})


test('Wrong transactions signature should be rejected', async () => {
  const sim = new Zemu(APP_PATH);
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
    tr.setPayoutAddress("asdasdassasadsada");
    tr.setPayoutExtraId("");
    tr.setCurrencyFrom("BTC");
    tr.setCurrencyTo("ETH");
    // 100000000 Satoshi to 48430000000000000000 Wei (1 BTC to 48.43 ETH)
    tr.setAmountToProvider(numberToBigEndianBuffer(100000000));
    tr.setAmountToWallet(numberToBigEndianBuffer(48430000000000000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    await swap.processTransaction(payload, 10000000);
    const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
    const signature: Buffer = secp256k1.sign(digest, swapTestPrivateKey).signature;
    const wrongSign: Buffer = secp256k1.signatureExport(signature);
    console.log(wrongSign.length);
    wrongSign.reverse();
    wrongSign[1] = wrongSign.length - 2;
    await expect(swap.checkTransactionSignature(wrongSign))
      .rejects.toEqual(new TransportStatusError(0x9d1a));
  } finally {
    await sim.close();
  }
})
