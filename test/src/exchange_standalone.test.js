// @flow
import "core-js/stable";
import "regenerator-runtime/runtime";

import Exchange from "./exchange.js";
import {
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
} from "./common";

import { zemu } from './test.fixture';

test('[Nano S] TransactionId should be 10 uppercase letters', zemu("nanos", async (sim) => {
  const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
  const transactionId: string = await swap.startNewTransaction();
  expect(transactionId.length).toBe(10);
  expect(transactionId).toBe(transactionId.toUpperCase());
}));

test('[Nano S] SetPartnerKey should not throw', zemu("nanos", async (sim) => {
  const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
  await swap.startNewTransaction();
  await expect(swap.setPartnerKey(partnerSerializedNameAndPubKey)).resolves.toBe(undefined);
}));

test('[Nano S] Wrong partner data signature should not be accepted', zemu("nanos", async (sim) => {
  const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
  await swap.startNewTransaction();
  await swap.setPartnerKey(partnerSerializedNameAndPubKey);
  await expect(swap.checkPartner(Buffer.alloc(70)))
    .rejects.toEqual(new TransportStatusError(0x9d1a));
}));

test('[Nano S] Correct signature of partner data should be accepted', zemu("nanos", async (sim) => {
  const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
  await swap.startNewTransaction();
  await swap.setPartnerKey(partnerSerializedNameAndPubKey);
  await expect(swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey)).resolves.toBe(undefined);
}));

test('[Nano S] Process transaction should not fail', zemu("nanos", async (sim) => {
  const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
  let transactionId = await swap.startNewTransaction();
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
}));

test('[Nano S] Transaction signature should be checked without errors', zemu("nanos", async (sim) => {
  const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
  let transactionId = await swap.startNewTransaction();
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
}));

test('[Nano S] transactions signature should be rejected', zemu("nanos", async (sim) => {
  const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.SWAP);
  let transactionId = await swap.startNewTransaction();
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
}));