import Btc from "@ledgerhq/hw-app-btc";
import secp256k1 from "secp256k1";
import secp256r1 from "secp256r1";
import sha256 from "js-sha256";
import "./protocol_pb.js";
import base64url from "base64url";

import {
    getSerializedAddressParametersBTC,
    getSerializedAddressParameters,
    fundTestPrivateKey, swapTestPrivateKey,
    partnerSerializedNameAndPubKey, DERSignatureOfPartnerNameAndPublicKey,
    fundPartnerSerializedNameAndPubKey, DERSignatureOfFundPartnerNameAndPublicKey,
    BTCConfig, BTCConfigSignature,
} from "./common";
import Exchange from "./exchange.js";
import {
    TRANSACTION_RATES,
    TRANSACTION_TYPES
} from "./exchange.js";

import Zemu from "@zondax/zemu";
import { waitForAppScreen, zemu } from './test.fixture';

// Forcing AmountToWallet to be bigger than 8B, so that the Bitcoin app would
// accept it only if the trim function works as expected
test('[Nano S] Overflow values should be trimmed when swaping', zemu("nanos", async (sim) => {
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
    // 1 BTC to 1 BTC
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

    await swap.signCoinTransaction();

    await Zemu.sleep(1000);

    let transport = await sim.getTransport();
}));

test('[Nano S] Overflow values should be trimmed when funding', zemu("nanos", async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.FUND);
    const transactionId_base64: string = await swap.startNewTransaction();
    const transactionId: Buffer = base64url.toBuffer(transactionId_base64);
    console.log("transactionID %s", transactionId.toString('hex'));

    await swap.setPartnerKey(fundPartnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfFundPartnerNameAndPublicKey);

    var tr = new proto.ledger_swap.NewFundResponse();

    tr.setUserId("John Doe");
    tr.setAccountName("Card 1234");
    tr.setInAddress("LKtSt6xfsmJMkPT8YyViAsDeRh7k8UfNjD");
    tr.setInCurrency("BTC");
    // 1 BTC
    tr.setInAmount(Buffer.from(['0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x05', '0xf5', '0xe1', '0x00']));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());

    const base64_payload: Buffer = Buffer.from(base64url(payload));

    await swap.processTransaction(base64_payload, 10000000);

    const message = Buffer.concat([Buffer.from('.'), base64_payload])
    const digest: Buffer = Buffer.from(sha256.sha256.array(message));
    const lol = secp256r1.sign(digest, fundTestPrivateKey).signature;

    process.stdout.write(JSON.stringify(lol) + '\n');

    const signature = secp256r1.signatureExport(lol)
    //console.log("Length of generated signature %d", sigTemp.length)

    process.stdout.write(JSON.stringify(signature) + '\n');

    await swap.checkTransactionSignature(signature);

    // useless what to put instead?
    const btcAddressParams = await getSerializedAddressParametersBTC("84'/0'/0'/1/0", "bech32");

    const checkAssetIn = swap.checkPayoutAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);

    // Wait until we are not in the main menu
    await waitForAppScreen(sim);
    await sim.navigateAndCompareSnapshots('.', 'nanos_valid_funding_is_accepted', [5, 0]);

    await swap.signCoinTransaction();
}));
