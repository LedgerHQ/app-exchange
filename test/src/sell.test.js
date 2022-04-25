import "core-js/stable";
import "regenerator-runtime/runtime";
import "./protocol_pb.js";

import {
    numberToBigEndianBuffer,
    BTC_INFO,
    XTZ_INFO,
    ETH_INFO,
} from "./common";

import { ExchangeTransactionPerformer } from "./ExchangeTransactionPerformer"

import { zemu, nano_environments } from './test.fixture';

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] SELL Valid Bitcoin selling transaction should be accepted`, zemu(model, async (sim) => {
        let t = new ExchangeTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(BTC_INFO);
        t.setToCurrencyInfo(XTZ_INFO);
        // 1 BTC
        t.setInAmount(numberToBigEndianBuffer(100000000));
        // 777 x 10^-2
        t.setOutAmount(777, 2);
        t.setFee(10000000);
        await t.performSell();
    }))
});


nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] SELL Overflow values should be trimmed when selling`, zemu(model, async (sim) => {
        let t = new ExchangeTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(BTC_INFO);
        t.setToCurrencyInfo(XTZ_INFO);
        // 1 BTC with 0x00 padding in front to ensure amount is trimmed properly
        t.setInAmount(Buffer.from(['0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x05', '0xf5', '0xe1', '0x00']));
        // 777 x 10^-2
        t.setOutAmount(777, 2);
        t.setFee(10000000);
        await t.performSell();
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] SELL Valid Ethereum selling transaction should be accepted`, zemu(model, async (sim) => {
        let t = new ExchangeTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(ETH_INFO);
        t.setToCurrencyInfo(XTZ_INFO);
        // 1 ETH
        t.setInAmount(numberToBigEndianBuffer(1000000000000000000));
        // 777 x 10^-2
        t.setOutAmount(777, 2);
        t.setFee(1000000000000000000);
        await t.performSell();
    }))
});
