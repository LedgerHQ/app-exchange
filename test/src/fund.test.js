import "core-js/stable";
import "regenerator-runtime/runtime";
import "./protocol_pb.js";

import {
    numberToBigEndianBuffer,
    BTC_INFO,
    ETH_INFO,
} from "./common";

import { SwapTransactionPerformer } from "./SwapTransactionPerformer"

import { zemu, nano_environments } from './test.fixture';

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] FUND Valid Bitcoin funding transaction should be accepted`, zemu(model, async (sim) => {
        let t = new SwapTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(BTC_INFO);
        // 1 BTC
        t.setInAmount(numberToBigEndianBuffer(100000000));
        t.setFee(10000000);
        await t.performFund();
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] FUND Overflow values should be trimmed when funding`, zemu(model, async (sim) => {
        let t = new SwapTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(BTC_INFO);
        // 1 BTC with 0x00 padding in front to ensure amount is trimmed properly
        t.setInAmount(Buffer.from(['0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x05', '0xf5', '0xe1', '0x00']));
        t.setFee(10000000);
        await t.performFund();
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] FUND Valid Ethereum funding transaction should be accepted`, zemu(model, async (sim) => {
        let t = new SwapTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(ETH_INFO);
        // 1 ETH
        t.setInAmount(numberToBigEndianBuffer(1000000000000000000));
        t.setFee(1000000000000000000);
        await t.performFund();
    }))
});
