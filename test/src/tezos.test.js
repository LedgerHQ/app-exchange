import "core-js/stable";
import "regenerator-runtime/runtime";
import "./protocol_pb.js";
import {
    BTC_INFO,
    XTZ_INFO,
} from "./common";

import { ExchangeTransactionPerformer } from "./ExchangeTransactionPerformer"

import { zemu, nano_environments } from './test.fixture';

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Tezos wrong payout address should not be accepted`, zemu(model, async (sim) => {
        let t = new ExchangeTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(BTC_INFO);
        t.setToCurrencyInfo(XTZ_INFO);
        t.setAmountToProvider(100000000);
        t.setAmountToWallet(1000000000);
        t.setFee(10000000);
        await t.performInvalidPayoutTransaction();
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Tezos valid payout address should be accepted`, zemu(model, async (sim) => {
        let t = new ExchangeTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(BTC_INFO);
        t.setToCurrencyInfo(XTZ_INFO);
        t.setAmountToProvider(100000000);
        t.setAmountToWallet(1000000000);
        t.setFee(10000000);
        await t.performValidPayoutTransaction();
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Tezos wrong refund address should be rejected`, zemu(model, async (sim) => {
        let t = new ExchangeTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(XTZ_INFO);
        t.setToCurrencyInfo(XTZ_INFO);
        t.setAmountToProvider(100000000);
        t.setAmountToWallet(1000000000);
        t.setFee(10000000);
        await t.performInvalidRefundTransaction();
    }))
});

nano_environments.forEach(function(model) {
    test(`[Nano ${model.letter}] Tezos valid refund address should be accepted`, zemu(model, async (sim) => {
        let t = new ExchangeTransactionPerformer(model, sim);
        t.setFromCurrencyInfo(XTZ_INFO);
        t.setToCurrencyInfo(XTZ_INFO);
        t.setAmountToProvider(100000000);
        t.setAmountToWallet(1000000000);
        t.setFee(10000000);
        await t.performValidPayoutValidRefundTransaction();
    }))
});
