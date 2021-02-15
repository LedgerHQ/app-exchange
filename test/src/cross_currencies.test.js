import "core-js/stable";
import "regenerator-runtime/runtime";
import Btc from "@ledgerhq/hw-app-btc";
import Eth from "@ledgerhq/hw-app-eth";
import Xrp from "@ledgerhq/hw-app-xrp";
import Xlm from "@ledgerhq/hw-app-str";
import { byContractAddress } from "@ledgerhq/hw-app-eth/erc20";
import secp256k1 from "secp256k1";
import sha256 from "js-sha256";
import "./protocol_pb.js";
import {
    getSerializedAddressParametersBTC,
    getSerializedAddressParameters,
    numberToBigEndianBuffer,
    swapTestPrivateKey,
    partnerSerializedNameAndPubKey, DERSignatureOfPartnerNameAndPublicKey,
    BTCConfig, BTCConfigSignature,
    LTCConfig, LTCConfigSignature,
    ETHConfig, ETHConfigSignature,
    AEConfig, AEConfigSignature,
    XRPConfig, XRPConfigSignature,
    XLMConfig, XLMConfigSignature
} from "./common";
import Exchange from "./exchange.js";
import {
    TransactionRate,
    TransactionType
} from "./exchange.js";
import Zemu from "@zondax/zemu";
import { TransportStatusError } from "@ledgerhq/errors";

const sim_options = {
    logging: true,
    start_delay: 4000,
    X11: true
};
const Resolve = require("path").resolve;
const APP_PATH = Resolve("elfs/exchange.elf");
const ALL_LIBS = { "Bitcoin": Resolve("elfs/bitcoin.elf"), "Litecoin": Resolve("elfs/litecoin.elf"), "Ethereum": Resolve("elfs/ethereum.elf"), "XRP": Resolve("elfs/xrp.elf"), "Stellar": Resolve("elfs/stellar.elf") };

test('Test BTC swap to LTC fails', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, ALL_LIBS);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TransactionType.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("34dZAvAf1ywuKj1iAydSpPtavigteo1T5G");
        tr.setPayinExtraId("");
        tr.setRefundAddress("bc1qwpgezdcy7g6khsald7cww42lva5g5dmasn6y2z");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("LKtSt6xfsmJMkPT8YyViAsDeRh7k8UfNjD");
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("BTC");
        tr.setCurrencyTo("LTC");
        tr.setAmountToProvider(numberToBigEndianBuffer(500000));
        tr.setAmountToWallet(numberToBigEndianBuffer(10000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 1070);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const ltcAddressParams = getSerializedAddressParametersBTC("49'/0'/0'/0/0");
        await swap.checkPayoutAddress(LTCConfig, LTCConfigSignature, ltcAddressParams.addressParameters);

        const btcAddressParams = getSerializedAddressParametersBTC("84'/0'/0'/1/0", "bech32");
        const checkRequest = swap.checkRefundAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickBoth();
        await expect(checkRequest).resolves.toBe(undefined);

        await swap.signCoinTransaction();

        await Zemu.sleep(1000);

        let transport = await sim.getTransport();

        try {
            var
                ans = await transport.send(0xe0, 0x44, 0x00, 0x02, Buffer.from('0100000002', 'hex')); // nVersion + number of inputs
            ans = await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('022d5a8829df3b90a541c8ae609fa9a0436e99b6a78a5c081e77c249ced0df3db200000000409c00000000000000', 'hex'));

            ans = await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('ffffff00', 'hex'));

            ans = await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('0252203e7659e8515db292f18f4aa0235822cb89d5de136c437fe8fca09945822e0000000040420f000000000000', 'hex'));

            ans = await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('ffffff00', 'hex'));

            ans = await transport.send(0xe0, 0x4a, 0xff, 0x00, Buffer.from('058000005480000000800000000000000100000000', 'hex'));

            ans = await transport.send(0xe0, 0x4a, 0x80, 0x00, Buffer.from('0220a107000000000017a9142040cc4169698b7f2f071e4ad14b01458bbc99b08732390800000000001600147051913704F2', 'hex'));
            ans = await transport.send(0xe0, 0x4a, 0x80, 0x00, Buffer.from('356BC3BF6FB0E7555F67688A377D', 'hex'));

            // start signing inputs
            ans = await transport.send(0xe0, 0x44, 0x00, 0x80, Buffer.from('0100000001', 'hex'));

            ans = await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('022d5a8829df3b90a541c8ae609fa9a0436e99b6a78a5c081e77c249ced0df3db200000000409c00000000000019', 'hex'));

            ans = await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('76a914a3f6421206f0448c113b9bb95ca48a70cee23b6888acffffff00', 'hex'));
            ans = await transport.send(0xe0, 0x48, 0x00, 0x00, Buffer.from('058000005480000000800000000000000000000000000000000001', 'hex'));

            console.log(ans);
        }
        catch (error) {
            expect(error["statusCode"]).toBe(0x6A8A)
        }
    } finally {
        await sim.close();
    }

})


test('Test LTC swap to ETH', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, ALL_LIBS);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TransactionType.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        var tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("MTmgECMPDEUHhtdjKTfd6GddwueYHyQYJw");
        tr.setPayinExtraId("");
        tr.setRefundAddress("MJovkMvQ2rXXUj7TGVvnQyVMWghSdqZsmu");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("LTC");
        tr.setCurrencyTo("ETH");
        tr.setAmountToProvider(numberToBigEndianBuffer(1234));
        tr.setAmountToWallet(numberToBigEndianBuffer((10 ** 18) * 0.04321)); // 10^18 wei == 1 ETH
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 17136);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const ethAddressParams = getSerializedAddressParameters("44'/60'/0'/0/0");
        await swap.checkPayoutAddress(ETHConfig, ETHConfigSignature, ethAddressParams.addressParameters);

        const ltcAddressParams = getSerializedAddressParametersBTC("49'/2'/0'/0/0", "p2sh");
        const checkRequest = swap.checkRefundAddress(LTCConfig, LTCConfigSignature, ltcAddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickBoth();
        await expect(checkRequest).resolves.toBe(undefined);

        await swap.signCoinTransaction();

        await Zemu.sleep(1000);

        let transport = await sim.getTransport();

        var ans = await transport.send(0xe0, 0x42, 0x00, 0x00, Buffer.from('000000000200000001', 'hex'));
        ans = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('4C0334A806A7AF557DF4968040BD86341DEE360010D4C400C7F838F43ED0F8EE010000006A', 'hex'));
        ans = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('47304402206C8878BEBDF2B69C0D6A037D1F1D405B22748921215EAB5A7197822502475A430220315058087ECAE5BF63DA6C', 'hex'));
        ans = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('3FD8F42C97355ADF1100E5335C9B13801F44D9E1B3012102AB8F0D66218556601E7B3CE19F6AC1BCB1A0F48CD5C2BC43DE6A', 'hex'));
        ans = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('9ABA056E0464FFFFFFFF', 'hex'));
        ans = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('02', 'hex'));
        ans = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('3911C4040000000017A91479EFD0A3CBF9840FD329DBAA667BC874891F1DE587', 'hex'));
        ans = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('024C6E3C000000001976A9146C2614C7B45EF8DFA8DC83E6739DDBE201D05AB088AC', 'hex'));
        let trusted_input = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('00000000', 'hex'));
        trusted_input = trusted_input.slice(0, -2).toString('hex');

        ans = await transport.send(0xe0, 0x44, 0x00, 0x02, Buffer.from('0100000001', 'hex'));
        ans = await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('0138' + trusted_input + '00', 'hex'));
        ans = await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('FFFFFFFF', 'hex'));

        ans = await transport.send(0xe0, 0x4a, 0xFF, 0x00, Buffer.from('058000003180000002800000000000000100000000', 'hex'));
        ans = await transport.send(0xe0, 0x4a, 0x00, 0x00, Buffer.from('02D20400000000000017A914D9F83A341518357BBC089B88A64F86C71A55BED28777C9C3040000000017A91410c8c0059a88', 'hex'));
        ans = await transport.send(0xe0, 0x4a, 0x80, 0x00, Buffer.from('dea62d5aa869f8f9c25e7054fe2c87', 'hex'));

        ans = await transport.send(0xe0, 0x44, 0x00, 0x80, Buffer.from('0100000001', 'hex'));
        ans = await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('0138' + trusted_input + '19', 'hex'));
        ans = await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('76A914C3722CEB74B4F5B583A690DDF05D01536B1CB8B488ACFFFFFFFF', 'hex'));

        await expect(transport.send(0xe0, 0x48, 0x00, 0x00, Buffer.from('05800000318000000280000000000000000000000C000000000001', 'hex')))
            .resolves.toEqual(
                Buffer.from('3045022100e01f45183c1e4fa647418420ae7dae7b6c1486377a0f9bc5530772a05a22206a02201194578e4d9bb4c137b7e072488a2ca50e4c85e1c4934785110b9ad8024f5038019000', 'hex')
            );


    } finally {
        await sim.close();
    }

})


test('Test ETH swap to BTC', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, ALL_LIBS);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TransactionType.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        let tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("0xd692Cb1346262F584D17B4B470954501f6715a82");
        tr.setPayinExtraId("");
        tr.setRefundAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("bc1qwpgezdcy7g6khsald7cww42lva5g5dmasn6y2z");
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("ETH");
        tr.setCurrencyTo("BTC");
        // 1 ETH to 1 BTC
        tr.setAmountToProvider(numberToBigEndianBuffer(1000000 * 1000000 * 1000000 * 1.1234)); // 10^18 wei == 1 ETH
        tr.setAmountToWallet(numberToBigEndianBuffer(100000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 840000000000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const btcAddressParams = getSerializedAddressParametersBTC("84'/0'/0'/1/0", "bech32");
        await swap.checkPayoutAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);

        const ethAddressParams = getSerializedAddressParameters("44'/60'/0'/0/0");
        const checkRequest = swap.checkRefundAddress(ETHConfig, ETHConfigSignature, ethAddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickBoth();
        await expect(checkRequest).resolves.toBe(undefined);

        await swap.signCoinTransaction();

        await Zemu.sleep(1000);

        let transport = await sim.getTransport();
        const eth = new Eth(transport);

        await expect(eth.signTransaction("44'/60'/0'/0/0", Buffer.from('ec808509502f900082520894d692cb1346262f584d17b4b470954501f6715a82880f971e5914ac800080018080', 'hex')))
            .resolves.toEqual({
                "r": "53bdfee62597cb9522d4a6b3b8a54e8b3d899c8694108959e845fb90e4a817ab",
                "s": "7c4a9bae5033c94effa9e46f76742909a96d2c886ec528a26efea9e60cdad38b",
                "v": "25"
            });

    } finally {
        await sim.close();
    }
})


test('Test Aeternity ERC20 swap to BTC', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, ALL_LIBS);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TransactionType.SWAP);
        jest.setTimeout(100000);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        let tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("0xd692Cb1346262F584D17B4B470954501f6715a82");
        tr.setPayinExtraId("");
        tr.setRefundAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("bc1qwpgezdcy7g6khsald7cww42lva5g5dmasn6y2z");
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("AE");
        tr.setCurrencyTo("BTC");
        // 1.1234 AE to 1 BTC
        tr.setAmountToProvider(numberToBigEndianBuffer(1000000 * 1000000 * 1000000 * 1.1234)); // 10^18 wei == 1 ETH
        tr.setAmountToWallet(numberToBigEndianBuffer(100000000));
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 1477845000000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const btcAddressParams = getSerializedAddressParametersBTC("84'/0'/0'/1/0", "bech32");
        await swap.checkPayoutAddress(BTCConfig, BTCConfigSignature, btcAddressParams.addressParameters);

        const aeAddressParams = getSerializedAddressParameters("44'/60'/0'/0/0");
        const checkRequest = swap.checkRefundAddress(AEConfig, AEConfigSignature, aeAddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickBoth();
        await expect(checkRequest).resolves.toBe(undefined);

        await swap.signCoinTransaction();

        await Zemu.sleep(1000);

        let transport = await sim.getTransport();

        const eth = new Eth(transport);
        const aeInfo = byContractAddress("0x5CA9a71B1d01849C0a95490Cc00559717fCF0D1d")
        if (aeInfo) await eth.provideERC20TokenInformation(aeInfo)

        await expect(eth.signTransaction("44'/60'/0'/0/0", Buffer.from('F8690385098BCA5A00828CCD945CA9a71B1d01849C0a95490Cc00559717fCF0D1d80B844A9059CBB000000000000000000000000d692Cb1346262F584D17B4B470954501f6715a820000000000000000000000000000000000000000000000000F971E5914AC8000038080', 'hex')))
            .resolves.toEqual({
                "r": "6e766ca0c8474da1dc5dc0d057e0f97711fd70aed7cb9965ff6dc423d8f4daad",
                "s": "63a0893b73e752965b65ebe13e1be8b5838e2113006656ea2eefa55fe0fa2919",
                "v": "2a"
            });

    } finally {
        await sim.close();
    }
})


test('Test XRP swap to ETH', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, ALL_LIBS);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TransactionType.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        let tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4");
        tr.setPayinExtraId("98765432");
        tr.setRefundAddress("rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("XRP");
        tr.setCurrencyTo("ETH");
        // 21 XRP to 1.1234 ETH
        tr.setAmountToProvider(numberToBigEndianBuffer(21000000)); // 1 xrp == 10^6 drops
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000 * 1000000 * 1000000 * 1.1234)); // 10^18 wei == 1 ETH
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 123);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const ethAddressParams = getSerializedAddressParameters("44'/60'/0'/0/0");
        await swap.checkPayoutAddress(ETHConfig, ETHConfigSignature, ethAddressParams.addressParameters);

        const xrpAddressParams = getSerializedAddressParameters("44'/144'/0'/1/0");
        const checkRequest = swap.checkRefundAddress(XRPConfig, XRPConfigSignature, xrpAddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickBoth();
        await expect(checkRequest).resolves.toBe(undefined);

        await swap.signCoinTransaction();

        await Zemu.sleep(1000);

        let transport = await sim.getTransport();

        const xrp = new Xrp(transport);

        await expect(xrp.signTransaction("44'/144'/0'/0/0", Buffer.from('120000228000000024038DE6A32E05E30A78201B0390AAB9614000000001406F4068400000000000007B7321038368B6F1151E0CD559126AE13910B8B8D790652EB5CC0B5019A63D2E6079296181143C0E955DFA24367806070434D8BE16A12E410C3B831422F866F3831E896120510409164B75B5673BF0F4', 'hex')))
            .resolves.toEqual("3045022100eefd26a52281c64a2b6d1d89f1e9a0aaeb1afe4aa3a55f4ed22d0a645d03e1ef0220632d06f22f8028c82f05b5ef46b10bd7851166b75c61582362001250fe89d18c");

    } finally {
        await sim.close();
    }
})


test('Test ETH swap to XRP', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, ALL_LIBS);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TransactionType.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        let tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("0xd692Cb1346262F584D17B4B470954501f6715a82");
        tr.setPayinExtraId("");
        tr.setRefundAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("rhBuYom8agWA4s7DFoM7AvsDA9XGkVCJz4");
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("ETH");
        tr.setCurrencyTo("XRP");
        // 1.1234 ETH to 21 XRP
        tr.setAmountToWallet(numberToBigEndianBuffer(21000000)); // 1 xrp == 10^6 drops
        tr.setAmountToProvider(numberToBigEndianBuffer(1000000 * 1000000 * 1000000 * 1.1234)); // 10^18 wei == 1 ETH
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 840000000000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const xrpAddressParams = getSerializedAddressParameters("44'/144'/0'/1/0");
        await swap.checkPayoutAddress(XRPConfig, XRPConfigSignature, xrpAddressParams.addressParameters);

        const ethAddressParams = getSerializedAddressParameters("44'/60'/0'/0/0");
        const checkRequest = swap.checkRefundAddress(ETHConfig, ETHConfigSignature, ethAddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickBoth();
        await expect(checkRequest).resolves.toBe(undefined);

        await swap.signCoinTransaction();

        await Zemu.sleep(1000);

        let transport = await sim.getTransport();
        const eth = new Eth(transport);

        await expect(eth.signTransaction("44'/60'/0'/0/0", Buffer.from('ec808509502f900082520894d692cb1346262f584d17b4b470954501f6715a82880f971e5914ac800080018080', 'hex')))
            .resolves.toEqual({
                "r": "53bdfee62597cb9522d4a6b3b8a54e8b3d899c8694108959e845fb90e4a817ab",
                "s": "7c4a9bae5033c94effa9e46f76742909a96d2c886ec528a26efea9e60cdad38b",
                "v": "25"
            });

    } finally {
        await sim.close();
    }
})

test('Test XLM swap to ETH', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, ALL_LIBS);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TransactionType.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        let tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("GC3JHKMIG7SWJEBAHFX35ILEFQJFSOKRSWFGTVXTPGCGDWG54FPXJ2Z6");
        tr.setPayinExtraId("123456789123456");
        tr.setRefundAddress("GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("XLM");
        tr.setCurrencyTo("ETH");
        // 1.1234567 XLM to 1.1234 ETH
        tr.setAmountToProvider(numberToBigEndianBuffer(11234567)); // 1 xlm == 10^7 drops
        tr.setAmountToWallet(numberToBigEndianBuffer(1000000 * 1000000 * 1000000 * 1.1234)); // 10^18 wei == 1 ETH
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 100);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const ethAddressParams = getSerializedAddressParameters("44'/60'/0'/0/0");
        await swap.checkPayoutAddress(ETHConfig, ETHConfigSignature, ethAddressParams.addressParameters);

        const xlmAddressParams = getSerializedAddressParameters("44'/148'/0'");
        const checkRequest = swap.checkRefundAddress(XLMConfig, XLMConfigSignature, xlmAddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickBoth();
        await expect(checkRequest).resolves.toBe(undefined);

        await swap.signCoinTransaction();

        await Zemu.sleep(1000);

        let transport = await sim.getTransport();

        const xlm = new Xlm(transport);

        await expect(xlm.signTransaction("44'/148'/0'", Buffer.from('7AC33997544E3175D266BD022439B22CDB16508C01163F26E5CB2A3E1045A97900000002000000009A222500CF47B03D05EDEC04ED3294CECE1DE727CCADB401F47D6B4B230E81A00000006401FA61520000000200000000000000010000000F3132333435363738393132333435360000000001000000000000000100000000B693A98837E5649020396fbea1642c12593951958a69d6f3798461d8dde15f74000000000000000000ab6d0700000000', 'hex')))
            .resolves.toEqual({
                "signature": Buffer.from("e5e0f224b5c9c85fa411c154f844cd309ee16af98a024ec65eb32e7d5a5b83e469b3085b6c3a4cf231d1e32733223a2a97c9b49fa9da1a58727301e562c90f0a", "hex")

            });

    } finally {
        await sim.close();
    }
})

test('Test ETH swap to XLM', async () => {
    jest.setTimeout(100000);
    const sim = new Zemu(APP_PATH, ALL_LIBS);
    try {
        await sim.start(sim_options);
        const swap = new Exchange(sim.getTransport(), TransactionType.SWAP);
        const transactionId: string = await swap.startNewTransaction();
        await swap.setPartnerKey(partnerSerializedNameAndPubKey);
        await swap.checkPartner(DERSignatureOfPartnerNameAndPublicKey);
        let tr = new proto.ledger_swap.NewTransactionResponse();
        tr.setPayinAddress("0xd692Cb1346262F584D17B4B470954501f6715a82");
        tr.setPayinExtraId("");
        tr.setRefundAddress("0xDad77910DbDFdE764fC21FCD4E74D71bBACA6D8D");
        tr.setRefundExtraId("");
        tr.setPayoutAddress("GCNCEJIAZ5D3APIF5XWAJ3JSSTHM4HPHE7GK3NAB6R6WWSZDB2A2BQ5B");
        tr.setPayoutExtraId("");
        tr.setCurrencyFrom("ETH");
        tr.setCurrencyTo("XLM");
        // 1.1234 ETH to 2.1 XLM
        tr.setAmountToWallet(numberToBigEndianBuffer(21000000)); // 1 xlm == 10^7 drops
        tr.setAmountToProvider(numberToBigEndianBuffer(1000000 * 1000000 * 1000000 * 1.1234)); // 10^18 wei == 1 ETH
        tr.setDeviceTransactionId(transactionId);

        const payload: Buffer = Buffer.from(tr.serializeBinary());
        await swap.processTransaction(payload, 840000000000000);
        const digest: Buffer = Buffer.from(sha256.sha256.array(payload));
        const signature: Buffer = secp256k1.signatureExport(secp256k1.sign(digest, swapTestPrivateKey).signature);
        await swap.checkTransactionSignature(signature);
        const xlmAddressParams = getSerializedAddressParameters("44'/148'/0'");
        await swap.checkPayoutAddress(XLMConfig, XLMConfigSignature, xlmAddressParams.addressParameters);

        const ethAddressParams = getSerializedAddressParameters("44'/60'/0'/0/0");
        const checkRequest = swap.checkRefundAddress(ETHConfig, ETHConfigSignature, ethAddressParams.addressParameters);
        // Wait until we are not in the main menu
        await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot());
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickRight();
        await sim.clickBoth();
        await expect(checkRequest).resolves.toBe(undefined);

        await swap.signCoinTransaction();

        await Zemu.sleep(1000);

        let transport = await sim.getTransport();
        const eth = new Eth(transport);

        await expect(eth.signTransaction("44'/60'/0'/0/0", Buffer.from('ec808509502f900082520894d692cb1346262f584d17b4b470954501f6715a82880f971e5914ac800080018080', 'hex')))
            .resolves.toEqual({
                "r": "53bdfee62597cb9522d4a6b3b8a54e8b3d899c8694108959e845fb90e4a817ab",
                "s": "7c4a9bae5033c94effa9e46f76742909a96d2c886ec528a26efea9e60cdad38b",
                "v": "25"
            });

    } finally {
        await sim.close();
    }
})
