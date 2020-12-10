const secp256k1 = require('secp256k1');
const sha256 = require('js-sha256').sha256;

const toHexPrintableConst = (buffer) => {
    var ans = "[0x" + buffer[0].toString(16).toUpperCase();
    for (i = 1; i < buffer.length; i++)
        ans += ", 0x" + buffer[i].toString(16).toUpperCase();
    ans += "]);"
    return ans;
}

const serializeSignedPartnerPublicKeyAndName = (partnerName, swapPartnerPublicKey, ledgerPrivateKey) => {
    var binaryPartnerName = Buffer.from(partnerName, 'ascii');
    var binaryNameAndPublicKey = Buffer.concat([Buffer.from([binaryPartnerName.length]), binaryPartnerName, swapPartnerPublicKey]);
    var hash = Buffer.from(sha256.sha256.array(binaryNameAndPublicKey));
    var signature = secp256k1.sign(hash, ledgerPrivateKey).signature;
    var der = secp256k1.signatureExport(signature)
    return { "privKey": "NONONO", "serializedPubKeyAndName": binaryNameAndPublicKey, "signatureInDER": der };
}

const createSignedPartnerPublicKeyAndName = (partnerName, ledgerPrivateKey) => {
    var swapPartnerPrivateKey = Buffer.from(sha256.sha256.array(partnerName));
    while (!secp256k1.privateKeyVerify(swapPartnerPrivateKey)) {
        swapPartnerPrivateKey = Buffer.from(sha256.sha256.array(swapPartnerPrivateKey));
    }

    const swapPartnerPublicKey = secp256k1.publicKeyCreate(swapPartnerPrivateKey, false);

    return { ...serializeSignedPartnerPublicKeyAndName(partnerName, swapPartnerPublicKey, ledgerPrivateKey), "privKey": swapPartnerPrivateKey, };
}

const createCurrencyConfig = (ticker, applicationName, coinConfig, ledgerPrivateKey) => {
    var payload = Buffer.concat([Buffer.from([ticker.length]), Buffer.from(ticker),
    Buffer.from([applicationName.length]), Buffer.from(applicationName),
    Buffer.from([coinConfig.length]), coinConfig]);
    var hash = Buffer.from(sha256.sha256.array(payload));
    var signature = secp256k1.sign(hash, ledgerPrivateKey).signature;
    var der = secp256k1.signatureExport(signature);
    return { "coinConfig": payload, "signature": der };
}

const main = () => {
    const changellyPubKey = secp256k1.publicKeyConvert(Buffer.from('0380d7c0d3a9183597395f58dda05999328da6f18fabd5cda0aff8e8e3fc633436', 'hex'), false)
    const oldLedgerTestPrivateKey = Buffer.from(sha256.sha256.array('Ledger'))
    const ledgerTestPrivateKey = Buffer.from('b1ed47ef58f782e2bc4d5abe70ef66d9009c2957967017054470e0f3e10f5833', 'hex')

    if (!secp256k1.privateKeyVerify(ledgerTestPrivateKey))
        throw new Error('Invalid ledger private key');

    const ledgerPublicKey = secp256k1.publicKeyCreate(ledgerTestPrivateKey);
    const uncompressed = secp256k1.publicKeyConvert(ledgerPublicKey, false)
    console.log("Ledger test private key: " + toHexPrintableConst(ledgerTestPrivateKey) + "\n")
    console.log("Ledger test compressed public key: " + toHexPrintableConst(ledgerPublicKey) + "\n");
    console.log("Ledger test public key: " + toHexPrintableConst(uncompressed) + "\n");
    console.log("===========\n");
    /*
    swapTestData = createSignedPartnerPublicKeyAndName("SWAP_TEST", ledgerTestPrivateKey);
    console.log("SWAP_TEST private key: " + toHexPrintableConst(swapTestData.privKey));
    console.log("SWAP_TEST signed name and pub key: " + toHexPrintableConst(swapTestData.serializedPubKeyAndName));
    console.log("DER signature: " + toHexPrintableConst(swapTestData.signatureInDER));
    console.log("===========\n");
    */
    changellyData = serializeSignedPartnerPublicKeyAndName("Changelly", changellyPubKey, ledgerTestPrivateKey);
    console.log("Changelly private key: " + toHexPrintableConst(changellyData.privKey));
    console.log("Changelly serialized name and pub key: " + toHexPrintableConst(changellyData.serializedPubKeyAndName));
    console.log("DER signature: " + toHexPrintableConst(changellyData.signatureInDER));

    var btcConfig = createCurrencyConfig("BTC", "Bitcoin", Buffer(0), ledgerTestPrivateKey);
    var ltcConfig = createCurrencyConfig("LTC", "Litecoin", Buffer(0), ledgerTestPrivateKey);
    var xrpConfig = createCurrencyConfig("XRP", "XRP", Buffer(0), ledgerTestPrivateKey);

    ethSubConfig = Buffer.concat([Buffer.from(["ETH".length]), Buffer.from("ETH"), Buffer.from([18])])
    var ethConfig = createCurrencyConfig("ETH", "Ethereum", ethSubConfig, ledgerTestPrivateKey);

    aeSubConfig = Buffer.concat([Buffer.from(["AE".length]), Buffer.from("AE"), Buffer.from([18])])
    var aeConfig = createCurrencyConfig("AE", "Ethereum", aeSubConfig, ledgerTestPrivateKey);

    usdtSubConfig = Buffer.concat([Buffer.from(["USDT".length]), Buffer.from("USDT"), Buffer.from([6])])
    var usdtConfig = createCurrencyConfig("USDT", "Ethereum", usdtSubConfig, ledgerTestPrivateKey);

    repSubConfig = Buffer.concat([Buffer.from(["REP".length]), Buffer.from("REP"), Buffer.from([18])])
    var repConfig = createCurrencyConfig("REP", "Ethereum", repSubConfig, ledgerTestPrivateKey);

    console.log("\nconst BTCConfig = Buffer.from(" + toHexPrintableConst(btcConfig.coinConfig));
    console.log("const BTCConfigSignature = Buffer.from(" + toHexPrintableConst(btcConfig.signature));
    console.log("\nconst LTCConfig = Buffer.from(" + toHexPrintableConst(ltcConfig.coinConfig));
    console.log("const LTCConfigSignature = Buffer.from(" + toHexPrintableConst(ltcConfig.signature));
    console.log("\nconst XRPConfig = Buffer.from(" + toHexPrintableConst(xrpConfig.coinConfig));
    console.log("const XRPConfigSignature = Buffer.from(" + toHexPrintableConst(xrpConfig.signature));
    console.log("\nconst ETHConfig = Buffer.from(" + toHexPrintableConst(ethConfig.coinConfig));
    console.log("const ETHConfigSignature = Buffer.from(" + toHexPrintableConst(ethConfig.signature));
    console.log("\nconst AEConfig = Buffer.from(" + toHexPrintableConst(aeConfig.coinConfig));
    console.log("const AEConfigSignature = Buffer.from(" + toHexPrintableConst(aeConfig.signature));
    console.log("\nconst USDTConfig = Buffer.from(" + toHexPrintableConst(usdtConfig.coinConfig));
    console.log("const USDTConfigSignature = Buffer.from(" + toHexPrintableConst(usdtConfig.signature));
    console.log("\nconst REPConfig = Buffer.from(" + toHexPrintableConst(repConfig.coinConfig));
    console.log("const REPConfigSignature = Buffer.from(" + toHexPrintableConst(repConfig.signature));
}


main();

