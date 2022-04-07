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
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(BTC_INFO);
    test.setToCurrencyInfo(XTZ_INFO);
    test.setAmountToProvider(100000000);
    test.setAmountToWallet(1000000000);
    test.setFee(10000000);
    await test.performInvalidPayoutTransaction();
}));

test(`[Nano S] Tezos valid payout address should be accepted`, zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(BTC_INFO);
    test.setToCurrencyInfo(XTZ_INFO);
    test.setAmountToProvider(100000000);
    test.setAmountToWallet(1000000000);
    test.setFee(10000000);
    await test.performValidPayoutTransaction();
}));

test(`[Nano S] Tezos wrong refund address should be rejected`, zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(XTZ_INFO);
    test.setToCurrencyInfo(XTZ_INFO);
    test.setAmountToProvider(100000000);
    test.setAmountToWallet(1000000000);
    test.setFee(10000000);
    await test.performInvalidRefundTransaction();
}));

test(`[Nano S] Tezos valid refund address should be accepted`, zemu(nano_environments[0], async (sim) => {
    var test = new SwapTransactionPerformer(nano_environments[0], sim);
    test.setFromCurrencyInfo(XTZ_INFO);
    test.setToCurrencyInfo(XTZ_INFO);
    test.setAmountToProvider(100000000);
    test.setAmountToWallet(1000000000);
    test.setFee(10000000);
    await test.performValidPayoutValidRefundTransaction();
}));
