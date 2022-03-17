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

const NANOS_ELF_PATH = Resolve('elfs/exchange_nanos.elf');
const NANOX_ELF_PATH = Resolve('elfs/exchange_nanox.elf');

/*
 Applications loaded for tests must comply with the following constraints:
 - starting with the name of the application (lowercase)
 - containing the Nano device type (lowercase)
 For tracking usage, it is also advised to keep the commit hash from where the application was built in the name
 For instance:

    bitcoin_nanos.284b9f9a98a91d31e48439d1f274a10302f6d8b7.elf
*/

const SIDELOADED_APPLICATIONS = {
    'bitcoin': 'Bitcoin',
    'ethereum': 'Ethereum',
    'litecoin': 'Litecoin',
    'stellar': 'Stellar',
    'xrp': 'XRP',
    'tezos': '"Tezos Wallet"'
};

function get_applications(nano_variant: string) {
    var applications = {};
    for (let path of dir.files('./elfs/', {sync: true})) {
        Object.entries(SIDELOADED_APPLICATIONS).forEach(
            ([file_prefix, name]) => {
                if (path.split('/')[1].startsWith(file_prefix) && path.includes(nano_variant)) {
                    applications[name] = path;
                }
            }
        );
    }
    return applications;
}

const NANOS_ETH_LIB = get_applications('nanos');
const NANOX_ETH_LIB = get_applications('nanox');

console.log(NANOS_ETH_LIB);

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
