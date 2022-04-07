import "core-js/stable";
import "regenerator-runtime/runtime";
import Btc from "@ledgerhq/hw-app-btc";
import Eth from "@ledgerhq/hw-app-eth";
import Xrp from "@ledgerhq/hw-app-xrp";
import Xlm from "@ledgerhq/hw-app-str";
import Xtz from "@ledgerhq/hw-app-tezos";
import { byContractAddress } from "@ledgerhq/hw-app-eth/erc20";
import "./protocol_pb.js";

import {
    ETH_INFO,
    AE_INFO,
    XRP_INFO,
    XLM_INFO,
    XTZ_INFO,
    LTC_INFO,
    LTC_LEGACY_INFO,
    BTC_INFO,
    BTC_LEGACY_INFO,
    BTC_NEWPROTOCOL_SEGWIT_INFO,
    BTC_NEWPROTOCOL_TAPROOT_INFO,
} from "./common";

import { AppClient as BtcAppAclient, PsbtV2, DefaultWalletPolicy } from "./AppBtc"

import { zemu, nano_environments } from './test.fixture';

import { SwapTransactionPerformer } from "./SwapTransactionPerformer"

test('[Nano S] BTC (legacy protocol) swap to LTC fails', zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(BTC_INFO);
    test.setToCurrencyInfo(LTC_LEGACY_INFO);
    test.setAmountToProvider(500000);
    test.setAmountToWallet(10000000);
    test.setFee(1070);
    await test.performSuccessfulTransaction();

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
    }
    catch (error) {
        expect(error["statusCode"]).toBe(0x6A8A)
    }
}));


test('[Nano S] LTC swap to ETH', zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(LTC_INFO);
    test.setToCurrencyInfo(ETH_INFO);
    test.setAmountToProvider(1234);
    test.setAmountToWallet((10 ** 18) * 0.04321); // 10^18 wei == 1 ETH
    test.setFee(17136);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    await transport.send(0xe0, 0x42, 0x00, 0x00, Buffer.from('000000000200000001', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('4C0334A806A7AF557DF4968040BD86341DEE360010D4C400C7F838F43ED0F8EE010000006A', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('47304402206C8878BEBDF2B69C0D6A037D1F1D405B22748921215EAB5A7197822502475A430220315058087ECAE5BF63DA6C', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('3FD8F42C97355ADF1100E5335C9B13801F44D9E1B3012102AB8F0D66218556601E7B3CE19F6AC1BCB1A0F48CD5C2BC43DE6A', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('9ABA056E0464FFFFFFFF', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('02', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('3911C4040000000017A91479EFD0A3CBF9840FD329DBAA667BC874891F1DE587', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('024C6E3C000000001976A9146C2614C7B45EF8DFA8DC83E6739DDBE201D05AB088AC', 'hex'));
    let trusted_input = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('00000000', 'hex'));
    trusted_input = trusted_input.slice(0, -2).toString('hex');

    await transport.send(0xe0, 0x44, 0x00, 0x02, Buffer.from('0100000001', 'hex'));
    await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('0138' + trusted_input + '00', 'hex'));
    await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('FFFFFFFF', 'hex'));

    await transport.send(0xe0, 0x4a, 0xFF, 0x00, Buffer.from('058000003180000002800000000000000100000000', 'hex'));
    await transport.send(0xe0, 0x4a, 0x00, 0x00, Buffer.from('02D20400000000000017A914D9F83A341518357BBC089B88A64F86C71A55BED28777C9C3040000000017A91410c8c0059a88', 'hex'));
    await transport.send(0xe0, 0x4a, 0x80, 0x00, Buffer.from('dea62d5aa869f8f9c25e7054fe2c87', 'hex'));

    await transport.send(0xe0, 0x44, 0x00, 0x80, Buffer.from('0100000001', 'hex'));
    await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('0138' + trusted_input + '19', 'hex'));
    await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('76A914C3722CEB74B4F5B583A690DDF05D01536B1CB8B488ACFFFFFFFF', 'hex'));

    await expect(transport.send(0xe0, 0x48, 0x00, 0x00, Buffer.from('05800000318000000280000000000000000000000C000000000001', 'hex')))
        .resolves.toEqual(Buffer.from('3045022100e01f45183c1e4fa647418420ae7dae7b6c1486377a0f9bc5530772a05a22206a02201194578e4d9bb4c137b7e072488a2ca50e4c85e1c4934785110b9ad8024f5038019000', 'hex'));
}));


test('[Nano S] BTC (legacy protocol) swap to ETH', zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(BTC_LEGACY_INFO);
    test.setToCurrencyInfo(ETH_INFO);
    test.setAmountToProvider(1234);
    test.setAmountToWallet((10 ** 18) * 0.04321); // 10^18 wei == 1 ETH
    test.setFee(17136);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    await transport.send(0xe0, 0x42, 0x00, 0x00, Buffer.from('000000000200000001', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('4C0334A806A7AF557DF4968040BD86341DEE360010D4C400C7F838F43ED0F8EE010000006A', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('47304402206C8878BEBDF2B69C0D6A037D1F1D405B22748921215EAB5A7197822502475A430220315058087ECAE5BF63DA6C', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('3FD8F42C97355ADF1100E5335C9B13801F44D9E1B3012102AB8F0D66218556601E7B3CE19F6AC1BCB1A0F48CD5C2BC43DE6A', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('9ABA056E0464FFFFFFFF', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('02', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('3911C4040000000017A91479EFD0A3CBF9840FD329DBAA667BC874891F1DE587', 'hex'));
    await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('024C6E3C000000001976A9146C2614C7B45EF8DFA8DC83E6739DDBE201D05AB088AC', 'hex'));
    let trusted_input = await transport.send(0xe0, 0x42, 0x80, 0x00, Buffer.from('00000000', 'hex'));
    trusted_input = trusted_input.slice(0, -2).toString('hex');

    await transport.send(0xe0, 0x44, 0x00, 0x02, Buffer.from('0100000001', 'hex'));
    await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('0138' + trusted_input + '00', 'hex'));
    await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('FFFFFFFF', 'hex'));

    await transport.send(0xe0, 0x4a, 0xFF, 0x00, Buffer.from('058000003180000000800000000000000100000000', 'hex'));
    await transport.send(0xe0, 0x4a, 0x00, 0x00, Buffer.from('02D20400000000000017A91438e09b5ad4d0f68563226ae8c0a0419aa6e8d94a8777C9C3040000000017A914bd7dcaf4d476', 'hex'));
    await transport.send(0xe0, 0x4a, 0x80, 0x00, Buffer.from('f9ea4f45d613b80e03f51b210fe087', 'hex'));

    await transport.send(0xe0, 0x44, 0x00, 0x80, Buffer.from('0100000001', 'hex'));
    await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('0138' + trusted_input + '19', 'hex'));
    await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('76A914C3722CEB74B4F5B583A690DDF05D01536B1CB8B488ACFFFFFFFF', 'hex'));

    await expect(transport.send(0xe0, 0x48, 0x00, 0x00, Buffer.from('05800000318000000080000000000000000000000C000000000001', 'hex')))
        .resolves.toEqual(Buffer.from('3045022100f48a6a9aed8354ad6d6d69bd8acf08c997b6fe46c222c214e66caf60b6e8d0a102201c4b0740fb47af7db9d5cdd51ac53a3f246fffac4e7d772176f95dcdbb2a0e08019000', 'hex'));
}));


test('[Nano S] ETH swap to BTC', zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(ETH_INFO);
    test.setToCurrencyInfo(BTC_INFO);
    test.setAmountToProvider(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
    test.setAmountToWallet(100000000);
    test.setFee(840000000000000);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    const eth = new Eth(transport);
    await expect(eth.signTransaction("44'/60'/0'/0/0", 'ec808509502f900082520894d692cb1346262f584d17b4b470954501f6715a82880f971e5914ac800080018080'))
        .resolves.toEqual({
            "r": "53bdfee62597cb9522d4a6b3b8a54e8b3d899c8694108959e845fb90e4a817ab",
            "s": "7c4a9bae5033c94effa9e46f76742909a96d2c886ec528a26efea9e60cdad38b",
            "v": "25"
        });
}));


test('[Nano S] Aeternity ERC20 swap to BTC', zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(AE_INFO);
    test.setToCurrencyInfo(BTC_INFO);
    // 1.1234 AE to 1 BTC
    test.setAmountToProvider(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
    test.setAmountToWallet(100000000);
    test.setFee(1477845000000000);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    const eth = new Eth(transport);
    const aeInfo = byContractAddress("0x5CA9a71B1d01849C0a95490Cc00559717fCF0D1d")
    if (aeInfo) await eth.provideERC20TokenInformation(aeInfo)

    await expect(eth.signTransaction("44'/60'/0'/0/0", 'F8690385098BCA5A00828CCD945CA9a71B1d01849C0a95490Cc00559717fCF0D1d80B844A9059CBB000000000000000000000000d692Cb1346262F584D17B4B470954501f6715a820000000000000000000000000000000000000000000000000F971E5914AC8000038080'))
        .resolves.toEqual({
            "r": "6e766ca0c8474da1dc5dc0d057e0f97711fd70aed7cb9965ff6dc423d8f4daad",
            "s": "63a0893b73e752965b65ebe13e1be8b5838e2113006656ea2eefa55fe0fa2919",
            "v": "2a"
        });
}));


test(`[Nano S] XRP swap to ETH`, zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(XRP_INFO);
    test.setToCurrencyInfo(ETH_INFO);
    // 21 XRP to 1.1234 ETH
    test.setAmountToProvider(21000000); // 1 xrp == 10^6 drops
    test.setAmountToWallet(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
    test.setFee(123);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    const xrp = new Xrp(transport);
    await expect(xrp.signTransaction("44'/144'/0'/0/0", '120000228000000024038DE6A32E05E30A78201B0390AAB9614000000001406F4068400000000000007B7321038368B6F1151E0CD559126AE13910B8B8D790652EB5CC0B5019A63D2E6079296181143C0E955DFA24367806070434D8BE16A12E410C3B831422F866F3831E896120510409164B75B5673BF0F4'))
        .resolves.toEqual("3045022100eefd26a52281c64a2b6d1d89f1e9a0aaeb1afe4aa3a55f4ed22d0a645d03e1ef0220632d06f22f8028c82f05b5ef46b10bd7851166b75c61582362001250fe89d18c"
        );
}));


test(`[Nano S] ETH swap to XRP`, zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(ETH_INFO);
    test.setToCurrencyInfo(XRP_INFO);
    // 1.1234 ETH to 21 XRP
    test.setAmountToProvider(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
    test.setAmountToWallet(21000000); // 1 xrp == 10^6 drops
    test.setFee(840000000000000);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    const eth = new Eth(transport);
    await expect(eth.signTransaction("44'/60'/0'/0/0", 'ec808509502f900082520894d692cb1346262f584d17b4b470954501f6715a82880f971e5914ac800080018080'))
        .resolves.toEqual({
            "r": "53bdfee62597cb9522d4a6b3b8a54e8b3d899c8694108959e845fb90e4a817ab",
            "s": "7c4a9bae5033c94effa9e46f76742909a96d2c886ec528a26efea9e60cdad38b",
            "v": "25"}
        );
}));


test(`[Nano S] XLM swap to ETH`, zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(XLM_INFO);
    test.setToCurrencyInfo(ETH_INFO);
    // 1.1234567 XLM to 1.1234 ETH
    test.setAmountToProvider(11234567); // 1 xlm == 10^7 drops
    test.setAmountToWallet(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
    test.setFee(100);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    const xlm = new Xlm(transport);
    await expect(xlm.signTransaction("44'/148'/0'", Buffer.from('7AC33997544E3175D266BD022439B22CDB16508C01163F26E5CB2A3E1045A97900000002000000009A222500CF47B03D05EDEC04ED3294CECE1DE727CCADB401F47D6B4B230E81A00000006401FA61520000000200000000000000010000000F3132333435363738393132333435360000000001000000000000000100000000B693A98837E5649020396fbea1642c12593951958a69d6f3798461d8dde15f74000000000000000000ab6d0700000000', 'hex')))
        .resolves.toEqual({
            "signature": Buffer.from("e5e0f224b5c9c85fa411c154f844cd309ee16af98a024ec65eb32e7d5a5b83e469b3085b6c3a4cf231d1e32733223a2a97c9b49fa9da1a58727301e562c90f0a", "hex")
        });
}));


test(`[Nano S] ETH swap to XLM`, zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(ETH_INFO);
    test.setToCurrencyInfo(XLM_INFO);
    // 1.1234567 XLM to 1.1234 ETH
    test.setAmountToProvider(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
    test.setAmountToWallet(21000000); // 1 xlm == 10^7 drops
    test.setFee(840000000000000);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    const eth = new Eth(transport);
    await expect(eth.signTransaction("44'/60'/0'/0/0", 'ec808509502f900082520894d692cb1346262f584d17b4b470954501f6715a82880f971e5914ac800080018080'))
        .resolves.toEqual({
            "r": "53bdfee62597cb9522d4a6b3b8a54e8b3d899c8694108959e845fb90e4a817ab",
            "s": "7c4a9bae5033c94effa9e46f76742909a96d2c886ec528a26efea9e60cdad38b",
            "v": "25"
        });
}));


test(`[Nano S] XTZ swap to ETH`, zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(XTZ_INFO);
    test.setToCurrencyInfo(ETH_INFO);
    // 0.0123 XTZ to 1.1234 ETH
    test.setAmountToProvider(0.0123 * 1000000); // 1 xtz == 10^6 microtez
    test.setAmountToWallet(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
    test.setFee(0.06 * 1000000);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    const xtz = new Xtz(transport);
    await expect(xtz.signOperation("44'/1729'/0'/0'", '032e3ed0be2a6f7e196f965f3915ef1afb8ac2316aa3e74ecad93a9328bab80f176b004035f49a9d068f852084ddf642835bbfdd4ff681b0ea01dae3d805d08c0100001dbfcc527042205a12508a62f37a72080e512c9338a9e7db3adeb6cae73e3ca56c004035f49a9d068f852084ddf642835bbfdd4ff681b0ea01dbe3d805d08c0181028c60000042cfe66ab45deadb496e7b8cddc172e2be0ad3b200'))
        .resolves.toEqual({
            "signature": "10b156dfed4f0934f3e0bbb4f62f9c78fb5bee84e685700d2f19f6bf9a5c9712d3b187ed87d0d78e03930dc8e66b78958c91e6bd71dfe6919adaf90f5dff270c"
        });
}));


test(`[Nano S] ETH swap to XTZ`, zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(ETH_INFO);
    test.setToCurrencyInfo(XTZ_INFO);
    // 1.1234 ETH to 2.1 XTZ
    test.setAmountToProvider(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
    test.setAmountToWallet(21000000); // 1 xtz == 10^6 microtez
    test.setFee(840000000000000);
    await test.performSuccessfulTransaction();

    let transport = await sim.getTransport();

    const eth = new Eth(transport);
    await expect(eth.signTransaction("44'/60'/0'/0/0", 'ec808509502f900082520894d692cb1346262f584d17b4b470954501f6715a82880f971e5914ac800080018080'))
        .resolves.toEqual({
            "r": "53bdfee62597cb9522d4a6b3b8a54e8b3d899c8694108959e845fb90e4a817ab",
            "s": "7c4a9bae5033c94effa9e46f76742909a96d2c886ec528a26efea9e60cdad38b",
            "v": "25"
        });
}));


// The following tests use the new protocol native to the Ledger 2.0.x application.

test('[Nano S] BTC (new protocol, segwit address) swap to ETH', zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(BTC_NEWPROTOCOL_SEGWIT_INFO);
    test.setToCurrencyInfo(ETH_INFO);
    test.setAmountToProvider(9999);
    test.setAmountToWallet((10 ** 18) * 0.04321);
    test.setFee(3);
    await test.performSuccessfulTransaction();

    const transport = await sim.getTransport();
    const appClient = new BtcAppAclient(transport);
    const psbt = new PsbtV2();

    const psbtBase64 = "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";

    psbt.deserialize(Buffer.from(psbtBase64, 'base64'));

    const policy = new DefaultWalletPolicy("wpkh(@0)", "[f5acc2fd/84'/0'/0']xpub6DUYn4moKgHkK2d7bXX3mHTPb6XQwRVFRMdZ6ZwLS5u3nonGVpJiFeZiQkHutwdFqxKP75jex8gvVm7ed4euYeDtMnoiF1Cz1z4CeBJYWin/**");

    const sigs = await appClient.signPsbt(psbt, policy, Buffer.alloc(32, 0));

    await expect(sigs.size).toEqual(2)
    await expect(sigs.get(0)).toEqual(Buffer.from("304402200ce6e00eeb7e54737a021240d6ccf63d1b3d07cbaa78d83356086042220fa70602201ea8c4f43a808be7a2ace708a46117cd98fa430cb7caca1d04b7849fefeeb64601", "hex"));
    await expect(sigs.get(1)).toEqual(Buffer.from("304402201eb8ae6458dd2d8bb596012cf6a2761be55824943cbecc72566f89a12564f706022029ec920b8e728ecd0c47194299ab77f6014af05924ad220c1ff48067eb4eac5501", "hex"));
}));


test('[Nano S] BTC (new protocol, taproot address) swap to ETH', zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(BTC_NEWPROTOCOL_TAPROOT_INFO);
    test.setToCurrencyInfo(ETH_INFO);
    test.setAmountToProvider(14460);
    test.setAmountToWallet((10 ** 18) * 0.04321); // 10^18 wei == 1 ETH
    test.setFee(114);
    await test.performSuccessfulTransaction();

    const transport = await sim.getTransport();
    const appClient = new BtcAppAclient(transport);
    const psbt = new PsbtV2();

    const psbtBase64 = "cHNidP8BAAoBAAAAAAAAAAAAAQIEAQAAAAEDBAAAAAABBAECAQUBAgH7BAIAAAAAAQEr1xEAAAAAAAAiUSD3Y9aVNfDDp/zNGyG5Rcy3gnt0PgEBedaYlLwQUziXogEOIFU4EAs2lLBmKvcTBNmyMYQ+evUOki7PVHbV4jFjld7AAQ8EAAAAAAEQBAAAAAABEgQAAAAAIRb3Y9aVNfDDp/zNGyG5Rcy3gnt0PgEBedaYlLwQUziXohkA9azC/VYAAIAAAACAAAAAgAEAAAC4IAAAAAEBK+c4AAAAAAAAIlEgcJAKXN6uSqujxSv/5/QCnBWS0zpq2smeWWCplTx/s8IBDiCyhHpHRzwa5b+9CkwpqRzrgBhXlnIM3le73HuL1cNKkwEPBAMAAAABEAQAAAAAARIEAAAAACEWcJAKXN6uSqujxSv/5/QCnBWS0zpq2smeWWCplTx/s8IZAPWswv1WAACAAAAAgAAAAIAAAAAApiMAAAABAwjQEQAAAAAAAAEEIlEgx9j622ryUFyy0KHN0W8KNsE2oan3VpvM6Uug+TvXmTshB8fY+ttq8lBcstChzdFvCjbBNqGp91abzOlLoPk715k7GQD1rML9VgAAgAAAAIAAAACAAQAAAAAAAAAAAQMIfDgAAAAAAAABBBYAFJyQ+TTqUfoPZQQXcEPgkI2mkpmDAA==";
    psbt.deserialize(Buffer.from(psbtBase64, 'base64'));

    const policy = new DefaultWalletPolicy("tr(@0)", "[f5acc2fd/86'/0'/0']xpub6C6unosUbSTkybyZTDLRNFKcWhcEWm5P6QdjuL26ZiL5mzt9c8eMHH3BGBCAhiaxMiC3h2xcMbdJjY7TbwtvxAhRfTTchyprB2JciaN6YrC/**");

    const sigs = await appClient.signPsbt(psbt, policy, Buffer.alloc(32, 0));

    await expect(sigs.size).toEqual(2)
    // taproot signatures are not deterministic, so they change at every execution
    // checking that the transaction was signed is anyway good enough
}));
