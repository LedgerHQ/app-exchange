import Zemu, {DeviceModel} from '@zondax/zemu';

const dir = require('node-dir')

const transactionUploadDelay = 60000;

async function waitForAppScreen(sim) {
    await sim.waitUntilScreenIsNot(sim.getMainMenuSnapshot(), transactionUploadDelay);
}

const sim_options = {
    // Uncomment for testing
    // logging: true,
    X11: true,
    startText: 'is ready',
    custom: '',
};

const Resolve = require('path').resolve;

const NANOS_ELF_PATH = Resolve('elfs/exchange_nanos.elf');
const NANOX_ELF_PATH = Resolve('elfs/exchange_nanox.elf');
const NANOSP_ELF_PATH = Resolve('elfs/exchange_nanosp.elf');

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
    'bitcoin_legacy': '"Bitcoin Legacy"',
    'ethereum': 'Ethereum',
    'litecoin': 'Litecoin',
    'stellar': 'Stellar',
    'xrp': 'XRP',
    'tezos_legacy': '"Tezos Wallet"'
};

function get_applications(nano_variant: string) {
    const applications = {};
    for (let path of dir.files('./elfs/', {sync: true})) {
        Object.entries(SIDELOADED_APPLICATIONS).forEach(
            ([file_prefix, name]) => {
                if (path.split('/')[1].startsWith(file_prefix + '_' + nano_variant + '.')) {
                    applications[name] = Resolve(path);
                }
            }
        );
    }
    return applications;
}

class ExchangeDeviceModel extends DeviceModel {
    letter: string;
    libs: string[];
    sdk: string;
}

const nano_environments: ExchangeDeviceModel[] = [
    { name: 'nanos', letter: 'S', path: NANOS_ELF_PATH, libs: get_applications('nanos'), sdk: '2.1'},
    { name: 'nanox', letter: 'X', path: NANOX_ELF_PATH, libs: get_applications('nanox'), sdk: '2.0.2'},
    { name: 'nanosp', letter: "SP", path: NANOSP_ELF_PATH, libs: get_applications('nanosp'), sdk: '1.0.3'},
];

const TIMEOUT = 1000000;

function zemu(device: ExchangeDeviceModel, func) {
    return async () => {
        jest.setTimeout(TIMEOUT);
        let zemu_args;
        zemu_args = [device.path, device.libs];
        const sim = new Zemu(...zemu_args);
        try {
            await sim.start({...sim_options, model: device.name, sdk: device.sdk});
            await func(sim);
        } finally {
            await sim.close();
        }
    };
}

module.exports = {
    zemu,
    waitForAppScreen,
    nano_environments
}
