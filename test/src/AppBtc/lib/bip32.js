"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.hardenedPathOf = exports.getXpubComponents = exports.pubkeyFromXpub = exports.pathStringToArray = exports.pathArrayToString = exports.bip32asBuffer = exports.pathElementsToBuffer = void 0;
const bip32_path_1 = __importDefault(require("bip32-path")); // TODO: get rid of this dependency
const bs58check_1 = __importDefault(require("bs58check"));
function pathElementsToBuffer(paths) {
    const buffer = Buffer.alloc(1 + paths.length * 4);
    buffer[0] = paths.length;
    paths.forEach((element, index) => {
        buffer.writeUInt32BE(element, 1 + 4 * index);
    });
    return buffer;
}
exports.pathElementsToBuffer = pathElementsToBuffer;
function bip32asBuffer(path) {
    const pathElements = !path ? [] : pathStringToArray(path);
    return pathElementsToBuffer(pathElements);
}
exports.bip32asBuffer = bip32asBuffer;
function pathArrayToString(pathElements) {
    // Limitation: bippath can't handle and empty path. It shouldn't affect us
    // right now, but might in the future.
    // TODO: Fix support for empty path.
    return bip32_path_1.default.fromPathArray(pathElements).toString();
}
exports.pathArrayToString = pathArrayToString;
function pathStringToArray(path) {
    return bip32_path_1.default.fromString(path).toPathArray();
}
exports.pathStringToArray = pathStringToArray;
function pubkeyFromXpub(xpub) {
    const xpubBuf = bs58check_1.default.decode(xpub);
    return xpubBuf.slice(xpubBuf.length - 33);
}
exports.pubkeyFromXpub = pubkeyFromXpub;
function getXpubComponents(xpub) {
    const xpubBuf = bs58check_1.default.decode(xpub);
    return {
        chaincode: xpubBuf.slice(13, 13 + 32),
        pubkey: xpubBuf.slice(xpubBuf.length - 33),
        version: xpubBuf.readUInt32BE(0),
    };
}
exports.getXpubComponents = getXpubComponents;
function hardenedPathOf(pathElements) {
    for (let i = pathElements.length - 1; i >= 0; i--) {
        if (pathElements[i] >= 0x80000000) {
            return pathElements.slice(0, i + 1);
        }
    }
    return [];
}
exports.hardenedPathOf = hardenedPathOf;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiYmlwMzIuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvbGliL2JpcDMyLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7Ozs7OztBQUFBLDREQUFpQyxDQUFDLG1DQUFtQztBQUNyRSwwREFBa0M7QUFFbEMsU0FBZ0Isb0JBQW9CLENBQUMsS0FBd0I7SUFDM0QsTUFBTSxNQUFNLEdBQUcsTUFBTSxDQUFDLEtBQUssQ0FBQyxDQUFDLEdBQUcsS0FBSyxDQUFDLE1BQU0sR0FBRyxDQUFDLENBQUMsQ0FBQztJQUNsRCxNQUFNLENBQUMsQ0FBQyxDQUFDLEdBQUcsS0FBSyxDQUFDLE1BQU0sQ0FBQztJQUN6QixLQUFLLENBQUMsT0FBTyxDQUFDLENBQUMsT0FBTyxFQUFFLEtBQUssRUFBRSxFQUFFO1FBQy9CLE1BQU0sQ0FBQyxhQUFhLENBQUMsT0FBTyxFQUFFLENBQUMsR0FBRyxDQUFDLEdBQUcsS0FBSyxDQUFDLENBQUM7SUFDL0MsQ0FBQyxDQUFDLENBQUM7SUFDSCxPQUFPLE1BQU0sQ0FBQztBQUNoQixDQUFDO0FBUEQsb0RBT0M7QUFFRCxTQUFnQixhQUFhLENBQUMsSUFBWTtJQUN4QyxNQUFNLFlBQVksR0FBRyxDQUFDLElBQUksQ0FBQyxDQUFDLENBQUMsRUFBRSxDQUFDLENBQUMsQ0FBQyxpQkFBaUIsQ0FBQyxJQUFJLENBQUMsQ0FBQztJQUMxRCxPQUFPLG9CQUFvQixDQUFDLFlBQVksQ0FBQyxDQUFDO0FBQzVDLENBQUM7QUFIRCxzQ0FHQztBQUVELFNBQWdCLGlCQUFpQixDQUFDLFlBQStCO0lBQy9ELDBFQUEwRTtJQUMxRSxzQ0FBc0M7SUFDdEMsb0NBQW9DO0lBQ3BDLE9BQU8sb0JBQU8sQ0FBQyxhQUFhLENBQUMsWUFBWSxDQUFDLENBQUMsUUFBUSxFQUFFLENBQUM7QUFDeEQsQ0FBQztBQUxELDhDQUtDO0FBRUQsU0FBZ0IsaUJBQWlCLENBQUMsSUFBWTtJQUM1QyxPQUFPLG9CQUFPLENBQUMsVUFBVSxDQUFDLElBQUksQ0FBQyxDQUFDLFdBQVcsRUFBRSxDQUFDO0FBQ2hELENBQUM7QUFGRCw4Q0FFQztBQUVELFNBQWdCLGNBQWMsQ0FBQyxJQUFZO0lBQ3pDLE1BQU0sT0FBTyxHQUFHLG1CQUFTLENBQUMsTUFBTSxDQUFDLElBQUksQ0FBQyxDQUFDO0lBQ3ZDLE9BQU8sT0FBTyxDQUFDLEtBQUssQ0FBQyxPQUFPLENBQUMsTUFBTSxHQUFHLEVBQUUsQ0FBQyxDQUFDO0FBQzVDLENBQUM7QUFIRCx3Q0FHQztBQUVELFNBQWdCLGlCQUFpQixDQUFDLElBQVk7SUFLNUMsTUFBTSxPQUFPLEdBQVcsbUJBQVMsQ0FBQyxNQUFNLENBQUMsSUFBSSxDQUFDLENBQUM7SUFDL0MsT0FBTztRQUNMLFNBQVMsRUFBRSxPQUFPLENBQUMsS0FBSyxDQUFDLEVBQUUsRUFBRSxFQUFFLEdBQUcsRUFBRSxDQUFDO1FBQ3JDLE1BQU0sRUFBRSxPQUFPLENBQUMsS0FBSyxDQUFDLE9BQU8sQ0FBQyxNQUFNLEdBQUcsRUFBRSxDQUFDO1FBQzFDLE9BQU8sRUFBRSxPQUFPLENBQUMsWUFBWSxDQUFDLENBQUMsQ0FBQztLQUNqQyxDQUFDO0FBQ0osQ0FBQztBQVhELDhDQVdDO0FBRUQsU0FBZ0IsY0FBYyxDQUM1QixZQUErQjtJQUUvQixLQUFLLElBQUksQ0FBQyxHQUFHLFlBQVksQ0FBQyxNQUFNLEdBQUcsQ0FBQyxFQUFFLENBQUMsSUFBSSxDQUFDLEVBQUUsQ0FBQyxFQUFFLEVBQUU7UUFDakQsSUFBSSxZQUFZLENBQUMsQ0FBQyxDQUFDLElBQUksVUFBVSxFQUFFO1lBQ2pDLE9BQU8sWUFBWSxDQUFDLEtBQUssQ0FBQyxDQUFDLEVBQUUsQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDO1NBQ3JDO0tBQ0Y7SUFDRCxPQUFPLEVBQUUsQ0FBQztBQUNaLENBQUM7QUFURCx3Q0FTQyJ9