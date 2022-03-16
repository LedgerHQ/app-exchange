import Zemu from '@zondax/zemu';

var dir = require('node-dir')

const transactionUploadDelay = 60000;

async function waitForAppScreen(sim) {
    await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot(), transactionUploadDelay);
}

const sim_options_nanos = {
    model: 'nanos',
    logging: true,
    X11: true,
    startDelay: 5000,
    startText: 'is ready',
    sdk: '2.1',
    custom: '',
};

const sim_options_nanox = {
    model: 'nanox',
    logging: true,
    X11: true,
    startDelay: 5000,
    startText: 'is ready',
    custom: '',
};

const Resolve = require('path').resolve;

const NANOS_ELF_PATH = Resolve('elfs/exchange.elf');
const NANOX_ELF_PATH = Resolve('elfs/exchange.elf');


const SIDELOADED_APPLICATIONS = {
    'bitcoin': 'Bitcoin',
    'ethereum': 'Ethereum',
    'litecoin': 'Litecoin',
    'stellar': 'Stellar',
    'xrp': 'XRP',
    'tezos': '"Tezos Wallet"'
};

var _applications = {};
for (let path of dir.files('./elfs/', {sync: true})) {
    Object.entries(SIDELOADED_APPLICATIONS).forEach(
        ([file_prefix, name]) => {
            if (path.split('/')[1].startsWith(file_prefix)) {
                _applications[name] = path
            }
        }
    );
}

const NANOS_ETH_LIB = _applications;
const NANOX_ETH_LIB = _applications;

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
