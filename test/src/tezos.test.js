import "core-js/stable";
import "regenerator-runtime/runtime";
import "./protocol_pb.js";
import {
    BTC_INFO,
    XTZ_INFO,
} from "./common";

import { SwapTransactionPerformer } from "./SwapTransactionPerformer"

import { zemu, nano_environments } from './test.fixture';

test(`[Nano S] Tezos wrong payout address should not be accepted`, zemu(nano_environments[0], async (sim) => {
    let t = new SwapTransactionPerformer(nano_environments[0], sim);
    t.setFromCurrencyInfo(BTC_INFO);
    t.setToCurrencyInfo(XTZ_INFO);
    t.setAmountToProvider(100000000);
    t.setAmountToWallet(1000000000);
    t.setFee(10000000);
    await t.performInvalidPayoutTransaction();
}));

test(`[Nano S] Tezos valid payout address should be accepted`, zemu(nano_environments[0], async (sim) => {
    let t = new SwapTransactionPerformer(nano_environments[0], sim);
    t.setFromCurrencyInfo(BTC_INFO);
    t.setToCurrencyInfo(XTZ_INFO);
    t.setAmountToProvider(100000000);
    t.setAmountToWallet(1000000000);
    t.setFee(10000000);
    await t.performValidPayoutTransaction();
}));

test(`[Nano S] Tezos wrong refund address should be rejected`, zemu(nano_environments[0], async (sim) => {
    let t = new SwapTransactionPerformer(nano_environments[0], sim);
    t.setFromCurrencyInfo(XTZ_INFO);
    t.setToCurrencyInfo(XTZ_INFO);
    t.setAmountToProvider(100000000);
    t.setAmountToWallet(1000000000);
    t.setFee(10000000);
    await t.performInvalidRefundTransaction();
}));

test(`[Nano S] Tezos valid refund address should be accepted`, zemu(nano_environments[0], async (sim) => {
    let t = new SwapTransactionPerformer(nano_environments[0], sim);
    t.setFromCurrencyInfo(XTZ_INFO);
    t.setToCurrencyInfo(XTZ_INFO);
    t.setAmountToProvider(100000000);
    t.setAmountToWallet(1000000000);
    t.setFee(10000000);
    await t.performValidPayoutValidRefundTransaction();
}));
