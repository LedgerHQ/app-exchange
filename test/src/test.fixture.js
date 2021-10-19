import Zemu from '@zondax/zemu';

const transactionUploadDelay = 60000;

async function waitForAppScreen(sim) {
    await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot(), transactionUploadDelay);
}

const sim_options_nanos = {
    model: 'nanos',
    logging: true,
    X11: true,
    startDelay: 5000,
    custom: '',
};

const sim_options_nanox = {
    model: 'nanox',
    logging: true,
    X11: true,
    startDelay: 5000,
    custom: '',
};

const Resolve = require('path').resolve;

const NANOS_ELF_PATH = Resolve('elfs/exchange.elf');
const NANOX_ELF_PATH = Resolve('elfs/exchange.elf');

const NANOS_ETH_LIB = { "Ethereum": 'elfs/ethereum.elf', "XRP": 'elfs/xrp.elf', "Stellar": 'elfs/stellar.elf', "Bitcoin": 'elfs/bitcoin.elf', "Litecoin": 'elfs/litecoin.elf', "\"Tezos Wallet\"": 'elfs/tezos.elf' };
const NANOX_ETH_LIB = { "Ethereum": 'elfs/ethereum.elf', "XRP": 'elfs/xrp.elf', "Stellar": 'elfs/stellar.elf', "Bitcoin": 'elfs/bitcoin.elf', "Litecoin": 'elfs/litecoin.elf', "\"Tezos Wallet\"": 'elfs/tezos.elf' };

const TIMEOUT = 1000000;

function zemu(device, func) {
    return async () => {
        jest.setTimeout(TIMEOUT);
        let zemu_args;
        let sim_options;
        if (device === "nanos") {
            zemu_args = [NANOS_ELF_PATH, NANOS_ETH_LIB];
            sim_options = sim_options_nanos;
        }
        else {
            zemu_args = [NANOX_ELF_PATH, NANOX_ETH_LIB];
            sim_options = sim_options_nanox;
        }
        const sim = new Zemu(...zemu_args);
        try {
            await sim.start(sim_options);
            await func(sim);
        } finally {
            await sim.close();
        }
    };
}

module.exports = {
    zemu,
    waitForAppScreen,
    NANOS_ELF_PATH,
    NANOX_ELF_PATH,
    NANOS_ETH_LIB,
    NANOX_ETH_LIB,
    sim_options_nanos,
    sim_options_nanox,
    TIMEOUT
}