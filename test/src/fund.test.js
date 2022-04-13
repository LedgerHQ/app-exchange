import "core-js/stable";
import "regenerator-runtime/runtime";
import secp256r1 from "secp256r1";
import sha256 from "js-sha256";
import "./protocol_pb.js";
import {
    getSerializedAddressParametersBTC,
    getSerializedAddressParameters,
    numberToBigEndianBuffer,
    fundTestPrivateKey,
    fundPartnerSerializedNameAndPubKey, DERSignatureOfFundPartnerNameAndPublicKey,
    BTCConfig, BTCConfigSignature,
    ETHConfig, ETHConfigSignature,
} from "./common"; import Exchange from "./exchange.js";
import {
    TRANSACTION_TYPES
} from "./exchange.js";
import base64url from "base64url";

export const ETHEREUM_DERIVATION_PATH = "44'/60'/0'/0/0";
export const ETHEREUM_PAYOUT_ADDRESS = "0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D";

import { waitForAppScreen, zemu, nano_environments } from './test.fixture';

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Valid Bitcoin funding transaction should be accepted`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.FUND);
        const transactionId_base64: string = await swap.startNewTransaction();
        const transactionId: Buffer = base64url.toBuffer(transactionId_base64);
        console.log("transactionID %s", transactionId.toString('hex'));

        await swap.setPartnerKey(fundPartnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfFundPartnerNameAndPublicKey);

        const tr = new proto.ledger_swap.NewFundResponse();

        tr.setUserId("John Doe");
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
        await sim.navigateAndCompareSnapshots('.', `${model.name}_valid_btc_funding_is_accepted`, [5, 0]);

        await swap.signCoinTransaction();
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Overflow values should be trimmed when funding`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.FUND);
        const transactionId_base64: string = await swap.startNewTransaction();
        const transactionId: Buffer = base64url.toBuffer(transactionId_base64);
        console.log("transactionID %s", transactionId.toString('hex'));

        await swap.setPartnerKey(fundPartnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfFundPartnerNameAndPublicKey);

        const tr = new proto.ledger_swap.NewFundResponse();

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
        const signature = secp256r1.signatureExport(secp256r1.sign(digest, fundTestPrivateKey).signature);

        await swap.checkTransactionSignature(signature);

        // useless what to put instead?
        const btcAddressParams = await getSerializedAddressParametersBTC("84'/0'/0'/1/0", "bech32");

        const checkAssetIn = swap.checkPayoutAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);

        // Wait until we are not in the main menu
        await waitForAppScreen(sim);
        await sim.navigateAndCompareSnapshots('.', `${model.name}_valid_btc_funding_is_accepted`, [5, 0]);
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Valid Ethereum funding transaction should be accepted`, zemu(model, async (sim) => {
        const swap = new Exchange(sim.getTransport(), TRANSACTION_TYPES.FUND);
        const transactionId_base64: string = await swap.startNewTransaction();
        const transactionId: Buffer = base64url.toBuffer(transactionId_base64);
        console.log("transactionID %s", transactionId.toString('hex'));

        await swap.setPartnerKey(fundPartnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfFundPartnerNameAndPublicKey);

        const tr = new proto.ledger_swap.NewFundResponse();
        tr.setUserId("John Doe");
        tr.setAccountName("Card 1234");
        tr.setInAddress(ETHEREUM_PAYOUT_ADDRESS);
        tr.setInCurrency("ETH");
        // 1 ETH
        tr.setInAmount(numberToBigEndianBuffer(1000000000000000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        const base64_payload: Buffer = Buffer.from(base64url(payload));

        await swap.processTransaction(base64_payload, 1000000000000000000);

        const message = Buffer.concat([Buffer.from('.'), base64_payload])
        const digest: Buffer = Buffer.from(sha256.sha256.array(message));

        const signature = secp256r1.signatureExport(secp256r1.sign(digest, fundTestPrivateKey).signature)

        await swap.checkTransactionSignature(signature);

        // useless what to put instead?
        const ethAddressParams = getSerializedAddressParameters(ETHEREUM_DERIVATION_PATH);

        const checkAssetIn = swap.checkPayoutAddress(ETHConfig, ETHConfigSignature, ethAddressParams.addressParameters);

        // Wait until we are not in the main menu
        await waitForAppScreen(sim);

        await sim.navigateAndCompareSnapshots('.', `${model.name}_valid_eth_funding_is_accepted`, [5, 0]);

        await swap.signCoinTransaction();
    }))
});
