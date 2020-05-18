"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.bip32asBuffer = bip32asBuffer;

var _bip32Path = _interopRequireDefault(require("bip32-path"));

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function bip32asBuffer(path) {
  const paths = !path ? [] : _bip32Path.default.fromString(path).toPathArray();
  let buffer = Buffer.alloc(1 + paths.length * 4);
  buffer[0] = paths.length;
  paths.forEach((element, index) => {
    buffer.writeUInt32BE(element, 1 + 4 * index);
  });
  return buffer;
}