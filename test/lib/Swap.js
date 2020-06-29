"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;

var _bignumber = require("bignumber.js");

const GET_VERSION_COMMAND = 0x00;
const START_NEW_TRANSACTION_COMMAND = 0x01;
const SET_PARTNER_KEY_COMMAND = 0x02;
const CHECK_PARTNER_COMMAND = 0x03;
const PROCESS_TRANSACTION_RESPONSE = 0x04;
const CHECK_TRANSACTION_SIGNATURE = 0x05;
const CHECK_PAYOUT_ADDRESS = 0x06;
const CHECK_REFUND_ADDRESS = 0x07;
const SIGN_COIN_TRANSACTION = 0x08;

class Swap {
  constructor(transport) {
    this.transport = transport;
    this.allowedStatuses = [0x9000, 0x6A80, 0x6A81, 0x6A82, 0x6A83, 0x6A84, 0x6A85, 0x6E00, 0x6D00, 0x9D1A];
  }

  isSuccess(result) {
    return result.length >= 2 && result.readUInt16BE(result.length - 2) == 0x9000;
  }

  mapProtocolError(result) {
    if (result.length < 2) throw new Error("Response length is too small");
    var errorMessage;

    switch (result.readUInt16BE(result.length - 2)) {
      case 0x6A80:
        errorMessage = "INCORRECT_COMMAND_DATA";
        break;

      case 0x6A81:
        errorMessage = "DESERIALIZATION_FAILED";
        break;

      case 0x6A82:
        errorMessage = "WRONG_TRANSACTION_ID";
        break;

      case 0x6A83:
        errorMessage = "INVALID_ADDRESS";
        break;

      case 0x6A84:
        errorMessage = "USER_REFUSED";
        break;

      case 0x6A85:
        errorMessage = "INTERNAL_ERROR";
        break;

      case 0x6E00:
        errorMessage = "CLASS_NOT_SUPPORTED";
        break;

      case 0x6D00:
        errorMessage = "INVALID_INSTRUCTION";
        break;

      case 0x9D1A:
        errorMessage = "SIGN_VERIFICATION_FAIL";
        break;

      default:
        errorMessage = "Unknown error";
        break;
    }

    throw new Error("Swap application report error " + errorMessage);
  }

  async getVersion() {
    let result = await this.transport.send(0xE0, GET_VERSION_COMMAND, 0x00, 0x00, Buffer(0), this.allowedStatuses);
    if (!this.isSuccess(result)) this.mapProtocolError(result);
    return result;
  }

  async startNewTransaction() {
    let result = await this.transport.send(0xE0, START_NEW_TRANSACTION_COMMAND, 0x00, 0x00, Buffer(0), this.allowedStatuses);
    if (!this.isSuccess(result)) this.mapProtocolError(result);
    if (result.length != 12) throw new Error("APDU response length should be 12");
    let transactionId = result.toString("ascii", 0, 10);
    return transactionId;
  }

  async setPartnerKey(partnerNameAndPublicKey) {
    let result = await this.transport.send(0xE0, SET_PARTNER_KEY_COMMAND, 0x00, 0x00, partnerNameAndPublicKey, this.allowedStatuses);
    if (!this.isSuccess(result)) this.mapProtocolError(result);
  }

  async checkPartner(signatureOfPartnerData) {
    let result = await this.transport.send(0xE0, CHECK_PARTNER_COMMAND, 0x00, 0x00, signatureOfPartnerData, this.allowedStatuses);
    if (!this.isSuccess(result)) this.mapProtocolError(result);
  }

  async processTransaction(transaction, fee) {
    var hex = fee.toString(16);
    hex = hex.padStart(hex.length + hex.length % 2, '0');
    var feeHex = Buffer.from(hex, 'hex');
    const bufferToSend = Buffer.concat([Buffer.from([transaction.length]), transaction, Buffer.from([feeHex.length]), feeHex]);
    console.log(bufferToSend.toString("hex"));
    let result = await this.transport.send(0xE0, PROCESS_TRANSACTION_RESPONSE, 0x00, 0x00, bufferToSend, this.allowedStatuses);
    if (!this.isSuccess(result)) this.mapProtocolError(result);
  }

  async checkTransactionSignature(transactionSignature) {
    let result = await this.transport.send(0xE0, CHECK_TRANSACTION_SIGNATURE, 0x00, 0x00, transactionSignature, this.allowedStatuses);
    if (!this.isSuccess(result)) this.mapProtocolError(result);
  }

  async checkPayoutAddress(payoutCurrencyConfig, currencyConfigSignature, addressParameters) {
    if (payoutCurrencyConfig.length > 255) {
      throw new Error("Currency config is too big");
    }

    if (currencyConfigSignature.length < 70 || currencyConfigSignature.length > 73) {
      throw new Error("Signature should be DER serialized and have length in [70, 73] bytes");
    }

    if (addressParameters.length > 255) {
      throw new Error("Address parameters is too big");
    }

    const bufferToSend = Buffer.concat([Buffer.from([payoutCurrencyConfig.length]), payoutCurrencyConfig, currencyConfigSignature, Buffer.from([addressParameters.length]), addressParameters]);
    let result = await this.transport.send(0xE0, CHECK_PAYOUT_ADDRESS, 0x00, 0x00, bufferToSend, this.allowedStatuses);
    if (!this.isSuccess(result)) this.mapProtocolError(result);
  }

  async checkRefundAddress(refundCurrencyConfig, currencyConfigSignature, addressParameters) {
    if (refundCurrencyConfig.length > 255) {
      throw new Error("Currency config is too big");
    }

    if (currencyConfigSignature.length < 70 || currencyConfigSignature.length > 73) {
      throw new Error("Signature should be DER serialized and have length in [70, 73] bytes");
    }

    if (addressParameters.length > 255) {
      throw new Error("Address parameters is too big");
    }

    const bufferToSend = Buffer.concat([Buffer.from([refundCurrencyConfig.length]), refundCurrencyConfig, currencyConfigSignature, Buffer.from([addressParameters.length]), addressParameters]);
    let result = await this.transport.send(0xE0, CHECK_REFUND_ADDRESS, 0x00, 0x00, bufferToSend, this.allowedStatuses);
    if (!this.isSuccess(result)) this.mapProtocolError(result);
  }

  async signCoinTransaction() {
    let result = await this.transport.send(0xE0, SIGN_COIN_TRANSACTION, 0x00, 0x00, Buffer(0), this.allowedStatuses);
    if (!this.isSuccess(result)) this.mapProtocolError(result);
  }

}

exports.default = Swap;