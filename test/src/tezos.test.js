import "core-js/stable";
import "regenerator-runtime/runtime";
import "./protocol_pb.js";
import {
    BTC_INFO,
    XTZ_INFO,
    XTZ_LEGACY_INFO,
} from "./common";

import { ExchangeTransactionPerformer } from "./ExchangeTransactionPerformer"

import { zemu, nano_environments } from './test.fixture';

const XTZ_variants = [{'name': 'normal', 'config': XTZ_INFO},
                      {'name': 'legacy', 'config': XTZ_LEGACY_INFO}];

XTZ_variants.forEach(function(variant) {
    nano_environments.forEach(function(model) {
        test(`[Nano ${model.letter}][Tezos ${variant.name}] Tezos wrong payout address should not be accepted`, zemu(model, async (sim) => {
            let t = new ExchangeTransactionPerformer(model, sim);
            t.setFromCurrencyInfo(BTC_INFO);
            t.setToCurrencyInfo(variant.config);
            t.setAmountToProvider(100000000);
            t.setAmountToWallet(1000000000);
            t.setFee(10000000);
            await t.performInvalidPayoutTransaction();
        }))
    });
});

XTZ_variants.forEach(function(variant) {
    nano_environments.forEach(function(model) {
        test(`[Nano ${model.letter}][Tezos ${variant.name}] Tezos valid payout address should be accepted`, zemu(model, async (sim) => {
            let t = new ExchangeTransactionPerformer(model, sim);
            t.setFromCurrencyInfo(BTC_INFO);
            t.setToCurrencyInfo(variant.config);
            t.setAmountToProvider(100000000);
            t.setAmountToWallet(1000000000);
            t.setFee(10000000);
            await t.performValidPayoutTransaction();
        }))
    });
});

XTZ_variants.forEach(function(variant) {
    nano_environments.forEach(function(model) {
        test(`[Nano ${model.letter}][Tezos ${variant.name}] Tezos wrong refund address should be rejected`, zemu(model, async (sim) => {
            let t = new ExchangeTransactionPerformer(model, sim);
            t.setFromCurrencyInfo(XTZ_INFO);
            t.setToCurrencyInfo(variant.config);
            t.setAmountToProvider(100000000);
            t.setAmountToWallet(1000000000);
            t.setFee(10000000);
            await t.performInvalidRefundTransaction();
        }))
    });
});

XTZ_variants.forEach(function(variant) {
    nano_environments.forEach(function(model) {
        test(`[Nano ${model.letter}][Tezos ${variant.name}] Tezos valid refund address should be accepted`, zemu(model, async (sim) => {
            let t = new ExchangeTransactionPerformer(model, sim);
            t.setFromCurrencyInfo(XTZ_INFO);
            t.setToCurrencyInfo(variant.config);
            t.setAmountToProvider(100000000);
            t.setAmountToWallet(1000000000);
            t.setFee(10000000);
            await t.performValidPayoutValidRefundTransaction();
        }))
    });
});
