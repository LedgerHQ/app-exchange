"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ClientCommandInterpreter = exports.GetMoreElementsCommand = exports.GetMerkleLeafIndexCommand = exports.GetMerkleLeafProofCommand = exports.GetPreimageCommand = exports.YieldCommand = void 0;
const bitcoinjs_lib_1 = require("bitcoinjs-lib");
const buffertools_1 = require("./buffertools");
const merkle_1 = require("./merkle");
const varint_1 = require("./varint");
var ClientCommandCode;
(function (ClientCommandCode) {
    ClientCommandCode[ClientCommandCode["YIELD"] = 16] = "YIELD";
    ClientCommandCode[ClientCommandCode["GET_PREIMAGE"] = 64] = "GET_PREIMAGE";
    ClientCommandCode[ClientCommandCode["GET_MERKLE_LEAF_PROOF"] = 65] = "GET_MERKLE_LEAF_PROOF";
    ClientCommandCode[ClientCommandCode["GET_MERKLE_LEAF_INDEX"] = 66] = "GET_MERKLE_LEAF_INDEX";
    ClientCommandCode[ClientCommandCode["GET_MORE_ELEMENTS"] = 160] = "GET_MORE_ELEMENTS";
})(ClientCommandCode || (ClientCommandCode = {}));
class ClientCommand {
}
class YieldCommand extends ClientCommand {
    constructor(results, progressCallback) {
        super();
        this.progressCallback = progressCallback;
        this.code = ClientCommandCode.YIELD;
        this.results = results;
    }
    execute(request) {
        this.results.push(Buffer.from(request.subarray(1)));
        if (this.progressCallback) {
            this.progressCallback();
        }
        return Buffer.from('');
    }
}
exports.YieldCommand = YieldCommand;
class GetPreimageCommand extends ClientCommand {
    constructor(known_preimages, queue) {
        super();
        this.code = ClientCommandCode.GET_PREIMAGE;
        this.known_preimages = known_preimages;
        this.queue = queue;
    }
    execute(request) {
        const req = Buffer.from(request.subarray(1));
        // we expect no more data to read
        if (req.length != 1 + 32) {
            throw new Error('Invalid request, unexpected trailing data');
        }
        if (req[0] != 0) {
            throw new Error('Unsupported request, the first byte should be 0');
        }
        // read the hash
        const hash = Buffer.alloc(32);
        for (let i = 0; i < 32; i++) {
            hash[i] = req[1 + i];
        }
        const req_hash_hex = hash.toString('hex');
        const known_preimage = this.known_preimages.get(req_hash_hex);
        if (known_preimage != undefined) {
            const preimage_len_varint = (0, varint_1.createVarint)(known_preimage.length);
            // We can send at most 255 - len(preimage_len_out) - 1 bytes in a single message;
            // the rest will be stored in the queue for GET_MORE_ELEMENTS
            const max_payload_size = 255 - preimage_len_varint.length - 1;
            const payload_size = Math.min(max_payload_size, known_preimage.length);
            if (payload_size < known_preimage.length) {
                for (let i = payload_size; i < known_preimage.length; i++) {
                    this.queue.push(Buffer.from([known_preimage[i]]));
                }
            }
            return Buffer.concat([
                preimage_len_varint,
                Buffer.from([payload_size]),
                Buffer.from(known_preimage.subarray(0, payload_size)),
            ]);
        }
        throw Error(`Requested unknown preimage for: ${req_hash_hex}`);
    }
}
exports.GetPreimageCommand = GetPreimageCommand;
class GetMerkleLeafProofCommand extends ClientCommand {
    constructor(known_trees, queue) {
        super();
        this.code = ClientCommandCode.GET_MERKLE_LEAF_PROOF;
        this.known_trees = known_trees;
        this.queue = queue;
    }
    execute(request) {
        const req = Buffer.from(request.subarray(1));
        if (req.length < 32 + 1 + 1) {
            throw new Error('Invalid request, expected at least 34 bytes');
        }
        const reqBuf = new buffertools_1.BufferReader(req);
        const hash = reqBuf.readSlice(32);
        const hash_hex = hash.toString('hex');
        let tree_size;
        let leaf_index;
        try {
            tree_size = (0, varint_1.sanitizeVarintToNumber)(reqBuf.readVarInt());
            leaf_index = (0, varint_1.sanitizeVarintToNumber)(reqBuf.readVarInt());
        }
        catch (e) {
            throw new Error("Invalid request, couldn't parse tree_size or leaf_index");
        }
        const mt = this.known_trees.get(hash_hex);
        if (!mt) {
            throw Error(`Requested Merkle leaf proof for unknown tree: ${hash_hex}`);
        }
        if (leaf_index >= tree_size || mt.size() != tree_size) {
            throw Error('Invalid index or tree size.');
        }
        if (this.queue.length != 0) {
            throw Error('This command should not execute when the queue is not empty.');
        }
        const proof = mt.getProof(leaf_index);
        const n_response_elements = Math.min(Math.floor((255 - 32 - 1 - 1) / 32), proof.length);
        const n_leftover_elements = proof.length - n_response_elements;
        // Add to the queue any proof elements that do not fit the response
        if (n_leftover_elements > 0) {
            this.queue.push(...proof.slice(-n_leftover_elements));
        }
        return Buffer.concat([
            mt.getLeafHash(leaf_index),
            Buffer.from([proof.length]),
            Buffer.from([n_response_elements]),
            ...proof.slice(0, n_response_elements),
        ]);
    }
}
exports.GetMerkleLeafProofCommand = GetMerkleLeafProofCommand;
class GetMerkleLeafIndexCommand extends ClientCommand {
    constructor(known_trees) {
        super();
        this.code = ClientCommandCode.GET_MERKLE_LEAF_INDEX;
        this.known_trees = known_trees;
    }
    execute(request) {
        const req = Buffer.from(request.subarray(1));
        if (req.length != 32 + 32) {
            throw new Error('Invalid request, unexpected trailing data');
        }
        // read the root hash
        const root_hash = Buffer.alloc(32);
        for (let i = 0; i < 32; i++) {
            root_hash[i] = req.readUInt8(i);
        }
        const root_hash_hex = root_hash.toString('hex');
        // read the leaf hash
        const leef_hash = Buffer.alloc(32);
        for (let i = 0; i < 32; i++) {
            leef_hash[i] = req.readUInt8(32 + i);
        }
        const leef_hash_hex = leef_hash.toString('hex');
        const mt = this.known_trees.get(root_hash_hex);
        if (!mt) {
            throw Error(`Requested Merkle leaf index for unknown root: ${root_hash_hex}`);
        }
        let leaf_index = 0;
        let found = 0;
        for (let i = 0; i < mt.size(); i++) {
            if (mt.getLeafHash(i).toString('hex') == leef_hash_hex) {
                found = 1;
                leaf_index = i;
                break;
            }
        }
        return Buffer.concat([Buffer.from([found]), (0, varint_1.createVarint)(leaf_index)]);
    }
}
exports.GetMerkleLeafIndexCommand = GetMerkleLeafIndexCommand;
class GetMoreElementsCommand extends ClientCommand {
    constructor(queue) {
        super();
        this.code = ClientCommandCode.GET_MORE_ELEMENTS;
        this.queue = queue;
    }
    execute(request) {
        if (request.length != 1) {
            throw new Error('Invalid request, unexpected trailing data');
        }
        if (this.queue.length === 0) {
            throw new Error('No elements to get');
        }
        // all elements should have the same length
        const element_len = this.queue[0].length;
        if (this.queue.some((el) => el.length != element_len)) {
            throw new Error('The queue contains elements with different byte length, which is not expected');
        }
        const max_elements = Math.floor(253 / element_len);
        const n_returned_elements = Math.min(max_elements, this.queue.length);
        const returned_elements = this.queue.splice(0, n_returned_elements);
        return Buffer.concat([
            Buffer.from([n_returned_elements]),
            Buffer.from([element_len]),
            ...returned_elements,
        ]);
    }
}
exports.GetMoreElementsCommand = GetMoreElementsCommand;
/**
 * This class will dispatch a client command coming from the hardware device to
 * the appropriate client command implementation. Those client commands
 * typically requests data from a merkle tree or merkelized maps.
 *
 * A ClientCommandInterpreter is prepared by adding the merkle trees and
 * merkelized maps it should be able to serve to the hardware device. This class
 * doesn't know anything about the semantics of the data it holds, it just
 * serves merkle data. It doesn't even know in what context it is being
 * executed, ie SignPsbt, getWalletAddress, etc.
 *
 * If the command yelds results to the client, as signPsbt does, the yielded
 * data will be accessible after the command completed by calling getYielded(),
 * which will return the yields in the same order as they came in.
 */
class ClientCommandInterpreter {
    constructor(progressCallback) {
        this.roots = new Map();
        this.preimages = new Map();
        this.yielded = [];
        this.queue = [];
        this.commands = new Map();
        const commands = [
            new YieldCommand(this.yielded, progressCallback),
            new GetPreimageCommand(this.preimages, this.queue),
            new GetMerkleLeafIndexCommand(this.roots),
            new GetMerkleLeafProofCommand(this.roots, this.queue),
            new GetMoreElementsCommand(this.queue),
        ];
        for (const cmd of commands) {
            if (this.commands.has(cmd.code)) {
                throw new Error(`Multiple commands with code ${cmd.code}`);
            }
            this.commands.set(cmd.code, cmd);
        }
    }
    getYielded() {
        return this.yielded;
    }
    addKnownPreimage(preimage) {
        this.preimages.set(bitcoinjs_lib_1.crypto.sha256(preimage).toString('hex'), preimage);
    }
    addKnownList(elements) {
        for (const el of elements) {
            const preimage = Buffer.concat([Buffer.from([0]), el]);
            this.addKnownPreimage(preimage);
        }
        const mt = new merkle_1.Merkle(elements.map((el) => (0, merkle_1.hashLeaf)(el)));
        this.roots.set(mt.getRoot().toString('hex'), mt);
    }
    addKnownMapping(mm) {
        this.addKnownList(mm.keys);
        this.addKnownList(mm.values);
    }
    execute(request) {
        if (request.length == 0) {
            throw new Error('Unexpected empty command');
        }
        const cmdCode = request[0];
        const cmd = this.commands.get(cmdCode);
        if (!cmd) {
            throw new Error(`Unexpected command code ${cmdCode}`);
        }
        return cmd.execute(request);
    }
}
exports.ClientCommandInterpreter = ClientCommandInterpreter;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY2xpZW50Q29tbWFuZHMuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvbGliL2NsaWVudENvbW1hbmRzLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7OztBQUFBLGlEQUF1QztBQUV2QywrQ0FBNkM7QUFDN0MscUNBQTRDO0FBRTVDLHFDQUFnRTtBQUVoRSxJQUFLLGlCQU1KO0FBTkQsV0FBSyxpQkFBaUI7SUFDcEIsNERBQVksQ0FBQTtJQUNaLDBFQUFtQixDQUFBO0lBQ25CLDRGQUE0QixDQUFBO0lBQzVCLDRGQUE0QixDQUFBO0lBQzVCLHFGQUF3QixDQUFBO0FBQzFCLENBQUMsRUFOSSxpQkFBaUIsS0FBakIsaUJBQWlCLFFBTXJCO0FBRUQsTUFBZSxhQUFhO0NBRzNCO0FBRUQsTUFBYSxZQUFhLFNBQVEsYUFBYTtJQUs3QyxZQUNFLE9BQWlCLEVBQ0EsZ0JBQTZCO1FBRTlDLEtBQUssRUFBRSxDQUFDO1FBRlMscUJBQWdCLEdBQWhCLGdCQUFnQixDQUFhO1FBSnZDLFNBQUksR0FBRyxpQkFBaUIsQ0FBQyxLQUFLLENBQUM7UUFPdEMsSUFBSSxDQUFDLE9BQU8sR0FBRyxPQUFPLENBQUM7SUFDekIsQ0FBQztJQUVELE9BQU8sQ0FBQyxPQUFlO1FBQ3JCLElBQUksQ0FBQyxPQUFPLENBQUMsSUFBSSxDQUFDLE1BQU0sQ0FBQyxJQUFJLENBQUMsT0FBTyxDQUFDLFFBQVEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDcEQsSUFBSSxJQUFJLENBQUMsZ0JBQWdCLEVBQUU7WUFDekIsSUFBSSxDQUFDLGdCQUFnQixFQUFFLENBQUM7U0FDekI7UUFDRCxPQUFPLE1BQU0sQ0FBQyxJQUFJLENBQUMsRUFBRSxDQUFDLENBQUM7SUFDekIsQ0FBQztDQUNGO0FBcEJELG9DQW9CQztBQUVELE1BQWEsa0JBQW1CLFNBQVEsYUFBYTtJQU1uRCxZQUFZLGVBQTRDLEVBQUUsS0FBZTtRQUN2RSxLQUFLLEVBQUUsQ0FBQztR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