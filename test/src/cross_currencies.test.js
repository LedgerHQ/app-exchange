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
    SHIB_INFO,
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

import { AppClient as BtcAppClient, PsbtV2, DefaultWalletPolicy } from "./AppBtc"

import { zemu, nano_environments } from './test.fixture';

import { ExchangeTransactionPerformer } from "./ExchangeTransactionPerformer"


nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] BTC (legacy protocol) swap to LTC fails`, zemu(model, async (sim) => {
        let transaction = new ExchangeTransactionPerformer(model, sim);
        transaction.setFromCurrencyInfo(BTC_LEGACY_INFO);
        transaction.setToCurrencyInfo(LTC_LEGACY_INFO);
        transaction.setAmountToProvider(500000);
        transaction.setAmountToWallet(10000000);
        transaction.setFee(1070);
        await transaction.performSuccessfulTransaction();

        let transport = await sim.getTransport();

        try {
            await transport.send(0xe0, 0x44, 0x00, 0x02, Buffer.from('0100000002', 'hex')); // nVersion + number of inputs
            await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('022d5a8829df3b90a541c8ae609fa9a0436e99b6a78a5c081e77c249ced0df3db200000000409c00000000000000', 'hex'));
            await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('ffffff00', 'hex'));
            await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('0252203e7659e8515db292f18f4aa0235822cb89d5de136c437fe8fca09945822e0000000040420f000000000000', 'hex'));
            await transport.send(0xe0, 0x44, 0x80, 0x02, Buffer.from('ffffff00', 'hex'));

            await transport.send(0xe0, 0x4a, 0xff, 0x00, Buffer.from('058000005480000000800000000000000100000000', 'hex'));
            await transport.send(0xe0, 0x4a, 0x80, 0x00, Buffer.from('0220a107000000000017a9142040cc4169698b7f2f071e4ad14b01458bbc99b08732390800000000001600147051913704F2', 'hex'));
            await transport.send(0xe0, 0x4a, 0x80, 0x00, Buffer.from('356BC3BF6FB0E7555F67688A377D', 'hex'));

            // start signing inputs
            await transport.send(0xe0, 0x44, 0x00, 0x80, Buffer.from('0100000001', 'hex'));
            await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('022d5a8829df3b90a541c8ae609fa9a0436e99b6a78a5c081e77c249ced0df3db200000000409c00000000000019', 'hex'));
            await transport.send(0xe0, 0x44, 0x80, 0x80, Buffer.from('76a914a3f6421206f0448c113b9bb95ca48a70cee23b6888acffffff00', 'hex'));

            await transport.send(0xe0, 0x48, 0x00, 0x00, Buffer.from('058000005480000000800000000000000000000000000000000001', 'hex'));
        }
        catch (error) {
            expect(error["statusCode"]).toBe(0x6A8A)
        }
    }))
});



nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] LTC swap to ETH`, zemu(model, async (sim) => {
        let transaction = new ExchangeTransactionPerformer(model, sim);
        transaction.setFromCurrencyInfo(LTC_INFO);
        transaction.setToCurrencyInfo(ETH_INFO);
        transaction.setAmountToProvider(1234);
        transaction.setAmountToWallet((10 ** 18) * 0.04321); // 10^18 wei == 1 ETH
        transaction.setFee(17136);
        await transaction.performSuccessfulTransaction();

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
    }))
});



nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] BTC (legacy protocol) swap to ETH`, zemu(model, async (sim) => {
        let transaction = new ExchangeTransactionPerformer(model, sim);
        transaction.setFromCurrencyInfo(BTC_LEGACY_INFO);
        transaction.setToCurrencyInfo(ETH_INFO);
        transaction.setAmountToProvider(1234);
        transaction.setAmountToWallet((10 ** 18) * 0.04321); // 10^18 wei == 1 ETH
        transaction.setFee(17136);
        await transaction.performSuccessfulTransaction();

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
    }))
});


nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Aeternity ERC20 swap to BTC`, zemu(model, async (sim) => {
        let transaction = new ExchangeTransactionPerformer(model, sim);
        transaction.setFromCurrencyInfo(AE_INFO);
        transaction.setToCurrencyInfo(BTC_INFO);
        // 1.1234 AE to 1 BTC
        transaction.setAmountToProvider(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
        transaction.setAmountToWallet(100000000);
        transaction.setFee(1477845000000000);
        await transaction.performSuccessfulTransaction();

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
    }))
});


nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Swap from AE ERC20 to ETH`, zemu(model, async (sim) => {
        const transaction = new ExchangeTransactionPerformer(model, sim);
        transaction.setFromCurrencyInfo(AE_INFO);
        transaction.setToCurrencyInfo(ETH_INFO);
        // 1.1234 AE to 1 BTC
        transaction.setAmountToProvider(1000000 * 1000000 * 1000000 * 1.1234); // 10^18 wei == 1 ETH
        transaction.setAmountToWallet(100000000);
        transaction.setFee(1477845000000000);
        await transaction.performSuccessfulTransaction();

        const transport = await sim.getTransport();

        const eth = new Eth(transport);
        const aeInfo = byContractAddress("0x5CA9a71B1d01849C0a95490Cc00559717fCF0D1d");
        if (aeInfo) await eth.provideERC20TokenInformation(aeInfo);

        await expect(eth.signTransaction("44'/60'/0'/0/0", 'F8690385098BCA5A00828CCD945CA9a71B1d01849C0a95490Cc00559717fCF0D1d80B844A9059CBB000000000000000000000000d692Cb1346262F584D17B4B470954501f6715a820000000000000000000000000000000000000000000000000F971E5914AC8000038080'))
            .resolves.toEqual({
                "r": "6e766ca0c8474da1dc5dc0d057e0f97711fd70aed7cb9965ff6dc423d8f4daad",
                "s": "63a0893b73e752965b65ebe13e1be8b5838e2113006656ea2eefa55fe0fa2919",
                "v": "2a"
            });
    }))
});


nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Swap from ETH to SHIB ERC20, large amount does not overflow`, zemu(model, async (sim) => {
        const transaction = new ExchangeTransactionPerformer(model, sim);
        transaction.setFromCurrencyInfo(ETH_INFO);
        transaction.setToCurrencyInfo(SHIB_INFO);
        // 1.1234 AE to 1 BTC
        transaction.setAmountToProvider(1000000 * 1000000 * 1000000 * 0.3); // 10^18 wei == 1 ETH
        transaction.setAmountToWallet(1000000 * 1000000 * 1000000 * 2318520.24);
        transaction.setFee(1477845000000000);
        const right_clicks = (model.letter ==  'S' ? 6 : 4);
        await transaction.performSuccessfulTransaction(right_clicks);
    }))
});


// The following tests use the new protocol native to the Ledger 2.0.x application.

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] BTC (new protocol, segwit address) swap to ETH`, zemu(model, async (sim) => {
        let transaction = new ExchangeTransactionPerformer(model, sim);
        transaction.setFromCurrencyInfo(BTC_NEWPROTOCOL_SEGWIT_INFO);
        transaction.setToCurrencyInfo(ETH_INFO);
        transaction.setAmountToProvider(9999);
        transaction.setAmountToWallet((10 ** 18) * 0.04321);
        transaction.setFee(3);
        await transaction.performSuccessfulTransaction();

        const transport = await sim.getTransport();
        const appClient = new BtcAppClient(transport);
        const psbt = new PsbtV2();

        const psbtBase64 = "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";

        psbt.deserialize(Buffer.from(psbtBase64, 'base64'));

        const policy = new DefaultWalletPolicy("wpkh(@0)", "[f5acc2fd/84'/0'/0']xpub6DUYn4moKgHkK2d7bXX3mHTPb6XQwRVFRMdZ6ZwLS5u3nonGVpJiFeZiQkHutwdFqxKP75jex8gvVm7ed4euYeDtMnoiF1Cz1z4CeBJYWin/**");

        const sigs = await appClient.signPsbt(psbt, policy, Buffer.alloc(32, 0));

        await expect(sigs.size).toEqual(2)
        await expect(sigs.get(0)).toEqual(Buffer.from("304402200ce6e00eeb7e54737a021240d6ccf63d1b3d07cbaa78d83356086042220fa70602201ea8c4f43a808be7a2ace708a46117cd98fa430cb7caca1d04b7849fefeeb64601", "hex"));
        await expect(sigs.get(1)).toEqual(Buffer.from("304402201eb8ae6458dd2d8bb596012cf6a2761be55824943cbecc72566f89a12564f706022029ec920b8e728ecd0c47194299ab77f6014af05924ad220c1ff48067eb4eac5501", "hex"));
    }))
});


nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] BTC (new protocol, taproot address) swap to ETH`, zemu(model, async (sim) => {
        let transaction = new ExchangeTransactionPerformer(model, sim);
        transaction.setFromCurrencyInfo(BTC_NEWPROTOCOL_TAPROOT_INFO);
        transaction.setToCurrencyInfo(ETH_INFO);
        transaction.setAmountToProvider(14460);
        transaction.setAmountToWallet((10 ** 18) * 0.04321); // 10^18 wei == 1 ETH
        transaction.setFee(114);
        await transaction.performSuccessfulTransaction();

        const transport = await sim.getTransport();
        const appClient = new BtcAppClient(transport);
        const psbt = new PsbtV2();

        const psbtBase64 = "cHNidP8BAgQBAAAAAQMEAAAAAAEEAQIBBQECAfsEAgAAAAABASvXEQAAAAAAACJRIPdj1pU18MOn/M0bIblFzLeCe3Q+AQF51piUvBBTOJeiIRZlHkDg37NKVvUX220eaii3FpnOXzB64Ps7kYiWN4UQyRkA9azC/VYAAIAAAACAAAAAgAEAAAC4IAAAAQ4gVTgQCzaUsGYq9xME2bIxhD569Q6SLs9UdtXiMWOV3sABDwQAAAAAARAEAAAAAAESBAAAAAAAAQEr5zgAAAAAAAAiUSBwkApc3q5Kq6PFK//n9AKcFZLTOmrayZ5ZYKmVPH+zwiEWl/KoNvAcJhw4kM98TJ/hHI3RMM9HjLrLoPb97bc+Y8cZAPWswv1WAACAAAAAgAAAAIAAAAAApiMAAAEOILKEekdHPBrlv70KTCmpHOuAGFeWcgzeV7vce4vVw0qTAQ8EAwAAAAEQBAAAAAABEgQAAAAAAAEDCNARAAAAAAAAAQQiUSDH2PrbavJQXLLQoc3Rbwo2wTahqfdWm8zpS6D5O9eZOyEHRHrv4RXWNQsC8Q5MlvP0IIIoIvJDCgXiWWYUmUOKgZ4ZAPWswv1WAACAAAAAgAAAAIABAAAAAAAAAAABAwh8OAAAAAAAAAEEFgAUnJD5NOpR+g9lBBdwQ+CQjaaSmYMA";
        psbt.deserialize(Buffer.from(psbtBase64, 'base64'));

        const policy = new DefaultWalletPolicy("tr(@0)", "[f5acc2fd/86'/0'/0']xpub6C6unosUbSTkybyZTDLRNFKcWhcEWm5P6QdjuL26ZiL5mzt9c8eMHH3BGBCAhiaxMiC3h2xcMbdJjY7TbwtvxAhRfTTchyprB2JciaN6YrC/**");

        const sigs = await appClient.signPsbt(psbt, policy, Buffer.alloc(32, 0));

        await expect(sigs.size).toEqual(2)
        // taproot signatures are not deterministic, so they change at every execution
        // checking that the transaction was signed is anyway good enough
    }))
});
