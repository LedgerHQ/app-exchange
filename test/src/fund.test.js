import "core-js/stable";
import "regenerator-runtime/runtime";
import secp256r1 from "secp256k1";
import sha256 from "js-sha256";
import "./protocol_pb.js";
import {
    getSerializedAddressParametersBTC,
    numberToBigEndianBuffer,
    fundTestPrivateKey,
    fundPartnerSerializedNameAndPubKey, DERSignatureOfFundPartnerNameAndPublicKey,
    BTCConfig, BTCConfigSignature,
} from "./common"; import Exchange from "./exchange.js";
import {
    TRANSACTION_TYPES
} from "./exchange.js";
import base64url from "base64url";

import { waitForAppScreen, zemu } from './test.fixture';

test('[Nano S] Valid funding transaction should be accepted', zemu("nanos", async (sim) => {
    const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.FUND);
    const transactionId_base64: string = await swap.startNewTransaction();
    const transactionId: Buffer = base64url.toBuffer(transactionId_base64);
    console.log("transactionID %s", transactionId.toString('hex'));

    await swap.setPartnerKey(fundPartnerSerializedNameAndPubKey);
    await swap.checkPartner(DERSignatureOfFundPartnerNameAndPublicKey);

    var tr = new proto.ledger_swap.NewFundResponse();

    tr.setUserId("lcastillo");
    tr.setAccountName("Card 1234");
    tr.setInAddress("LKtSt6xfsmJMkPT8YyViAsDeRh7k8UfNjD");
    tr.setInCurrency("BTC");
    // 1 BTC
    tr.setInAmount(numberToBigEndianBuffer(100000000));
    tr.setDeviceTransactionId(transactionId);

    const payload: Buffer = Buffer.from(tr.serializeBinary());
    const base64_payload: Buffer = Buffer.from(base64url(payload));

    await swap.processTransaction(base64_payload, 10000000);

    const message = Buffer.concat([Buffer.from('.'), base64_payload])
    const digest: Buffer = Buffer.from(sha256.sha256.array(message));

    const signature = secp256r1.signatureExport(secp256r1.sign(digest, fundTestPrivateKey).signature)
    //console.log("Length of generated signature %d", sigTemp.length)

    //const signature: Buffer = secp256k1.signatureExport(sigTemp);
    //console.log("Length of exported signature %d", signature.length)

    await swap.checkTransactionSignature(signature);

    // useless what to put instead?
    const btcAddressParams = await getSerializedAddressParametersBTC("84'/0'/0'/1/0", "bech32");

    const checkAssetIn = swap.checkPayoutAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);

    // Wait until we are not in the main menu
    await waitForAppScreen(sim);
    await sim.navigateAndCompareSnapshots('.', 'nanos_xlm_valid_refund_address_is_accepted', [4, 0]);

    await swap.signCoinTransaction();
}));