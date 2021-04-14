const bitcoin = require('bitcoinjs-lib');
const bip39 = require('bip39')

const default_speculos_memonic = 'glory promote mansion idle axis finger extra february uncover one trip resource lawn turtle enact monster seven myth punch hobby comfort wild raise skin';
bip39.mnemonicToSeed(default_speculos_memonic).then(bytes => {
    var master_node = bitcoin.bip32.fromSeed(bytes)
    var derivedNode = master_node.derivePath("m/44'/0'/0'/0/0")
    var payment = bitcoin.payments.p2pkh({ pubkey: derivedNode.publicKey, network: bitcoin.networks.bitcoin });
    console.log(payment);
    console.log(payment.output);
    console.log(payment.input);
    var address = payment.address;
    console.log(address);
    var trHex = '010000000135f334eeb86a692ccd40df1536095067a9b37897b9ea7c251a5bf5f614987ed4000000006a47304402203e8870877b05685ec5023edc31fcb3eee6a9d2497ea7102afafe5a6270544d9c022058c92cddde2312c3c1e6955aca65d6e3d19efcbc7ad49bb8f5cc6c73997a5353012102f5507e2dcb6f2f54946743caea2023fa33ed6200aae7453659e00ac8899056faffffffff02007f0800000000001976a9149411c0ee59daeb403d700ff1b849d58fc0d34a5488aca378ff06000000001976a9148ab2c7fb59962365941c44eb3e43a3d2396d90de88ac00000000';
})
/*
var sh256=require('js-sha256');

var dSHA = function(x) {
    return Buffer.from(sh256.digest(sh256.digest(Buffer.from(x, 'hex'))));
}
const EL = require('elliptic').ec;
var el = new EL("secp256k1");
var key = el.keyFromPublic('025476c2e83188368da1ff3e292e7acafcdb3566bb0ad253f62fc70f07aeee6357', 'hex');
key.verify('sighHash', 'signature');
*/