const secp256k1 = require('secp256k1')
const sha256 = require('js-sha256').sha256

const toHexPrintableConst  = (buffer) => {
    var ans = "{0x" + buffer[0].toString(16).toUpperCase();
    for (i = 1; i < buffer.length; i++)
        ans += ", 0x" + buffer[i].toString(16).toUpperCase();
    ans +="}"
    return ans;
}

const createSignedPartnerPublicKeyAndName = (partnerName, ledgerPrivateKey) => {
    var swapPartnerPrivateKey = Buffer.from(sha256.sha256.array(partnerName));
    while (!secp256k1.privateKeyVerify(swapPartnerPrivateKey)) {
        swapPartnerPrivateKey = Buffer.from(sha256.sha256.array(swapPartnerPrivateKey));
    }

    const swapPartnerPublicKey = secp256k1.publicKeyCreate(swapPartnerPrivateKey, false);

    var binaryPartnerName = Buffer.from(partnerName, 'ascii');
    var binaryNameAndPublicKey = Buffer.concat([Buffer.from([binaryPartnerName.length]), binaryPartnerName, swapPartnerPublicKey]);
    var hash = Buffer.from(sha256.sha256.array(binaryNameAndPublicKey));
    var signature = secp256k1.sign(hash, ledgerPrivateKey).signature;
    var der = secp256k1.signatureExport(signature)
    return {"privKey":swapPartnerPrivateKey, "serializedPubKeyAndName": binaryNameAndPublicKey, "signatureInDER": der};
}

const createCurrencyConfig = (ticker, applicationName, coinConfig, ledgerPrivateKey) => {
    var payload = Buffer.concat([Buffer.from([ticker.length]), Buffer.from(ticker),
                                Buffer.from([applicationName.length]), Buffer.from(applicationName),
                                Buffer.from([coinConfig.length]), coinConfig]);
    var hash = Buffer.from(sha256.sha256.array(payload));
    var signature = secp256k1.sign(hash, ledgerPrivateKey).signature;
    var der = secp256k1.signatureExport(signature);
    return {"coinConfig":payload, "signature": der};
}

const main = () => {
    const ledgerPrivateKey = Buffer.from(sha256.sha256.array('Ledger'))

    if (!secp256k1.privateKeyVerify(ledgerPrivateKey))
        throw new Error('Invalid ledger private key');

    const ledgerPublicKey = secp256k1.publicKeyCreate(ledgerPrivateKey);
    const uncompressed = secp256k1.publicKeyConvert(ledgerPublicKey, false)
    console.log("Ledger private key: " + toHexPrintableConst(ledgerPrivateKey) + "\n")
    console.log("Ledger compressed public key: " + toHexPrintableConst(ledgerPublicKey) + "\n");
    console.log("Ledger public key: " + toHexPrintableConst(uncompressed) + "\n");
    console.log("===========\n");
    swapTestData = createSignedPartnerPublicKeyAndName("SWAP_TEST", ledgerPrivateKey);
    console.log("SWAP_TEST private key: " + toHexPrintableConst(swapTestData.privKey));
    console.log("SWAP_TEST signed name and pub key: " + toHexPrintableConst(swapTestData.serializedPubKeyAndName));
    console.log("DER signature: " + toHexPrintableConst(swapTestData.signatureInDER));
    console.log("===========\n");
    var btcConfig = createCurrencyConfig("BTC", "Bitcoin", Buffer(0), ledgerPrivateKey);
    var ltcConfig = createCurrencyConfig("LTC", "Litecoin", Buffer(0), ledgerPrivateKey);
    console.log("BTC config: " +toHexPrintableConst(btcConfig.coinConfig));
    console.log("BTC config signature: " +toHexPrintableConst(btcConfig.signature));
    console.log("LTC config: " +toHexPrintableConst(ltcConfig.coinConfig));
    console.log("LTC config signature: " +toHexPrintableConst(ltcConfig.signature));
}


main();

