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

    const swapPartnerPublicKey = secp256k1.publicKeyCreate(swapPartnerPrivateKey);

    var binaryPartnerName = Buffer.from(partnerName, 'ascii');
    var binaryNameAndPublicKey = Buffer.concat([Buffer.from([binaryPartnerName.length]), binaryPartnerName, swapPartnerPublicKey]);
    var signature = secp256k1.sign(Buffer.from(sha256.sha256.array(binaryNameAndPublicKey)), ledgerPrivateKey).signature.split();
    var der = Buffer.concat([Buffer.from([30, 68, 2, 32]), signature.slice(0, 32), Buffer.from([2, 32]), signature.slice(32, 32)]);
    return {"privKey":swapPartnerPrivateKey, "serializedPubKeyAndName": binaryNameAndPublicKey, "signatureInDER": der};
}

const main = () => {
    const ledgerPrivateKey = Buffer.from(sha256.sha256.array('Ledger'))

    if (!secp256k1.privateKeyVerify(ledgerPrivateKey))
        throw new Error('Invalid ledger private key');

    const ledgerPublicKey = secp256k1.publicKeyCreate(ledgerPrivateKey);
    const uncompressed = secp256k1.publicKeyConvert(ledgerPublicKey, false)
    
    console.log("Ledger public key: " + toHexPrintableConst(uncompressed));

    swapTestData = createSignedPartnerPublicKeyAndName("SWAP_TEST", ledgerPrivateKey);
    console.log("SWAP_TEST private key: " + toHexPrintableConst(swapTestData.privKey));
    console.log("SWAP_TEST signed name and pub key: " + toHexPrintableConst(swapTestData.serializedPubKeyAndName));
    console.log("DER signature: " + toHexPrintableConst(swapTestData.signatureInDER));
}


main();

