"use strict";
// packages/chatbot-backend-sdk/src/utils/crypto.ts
Object.defineProperty(exports, "__esModule", { value: true });
exports.HMACSignatureProvider = void 0;
var crypto = require("crypto");
var HMACSignatureProvider = /** @class */ (function () {
    function HMACSignatureProvider(apiKey, productId, signingSecret) {
        this.apiKey = apiKey;
        this.productId = productId;
        this.signingSecret = signingSecret;
    }
    /**
     * Generates signature headers containing signature, nonce, timestamp, product tenant ID, and API key.
     */
    HMACSignatureProvider.prototype.sign = function (payload) {
        var timestamp = Date.now().toString();
        var nonce = crypto.randomBytes(16).toString('hex');
        var signature = this.computeSignature(timestamp, nonce, payload);
        return {
            'X-Envoy-Signature': signature,
            'X-Envoy-Timestamp': timestamp,
            'X-Envoy-Nonce': nonce,
            'X-Envoy-API-Key': this.apiKey,
            'X-Envoy-Product-ID': this.productId
        };
    };
    /**
     * Verifies the authenticity of incoming payload by comparing computed and received signatures.
     */
    HMACSignatureProvider.prototype.verify = function (payload, headers) {
        var signature = headers['x-envoy-signature'] || headers['X-Envoy-Signature'];
        var timestamp = headers['x-envoy-timestamp'] || headers['X-Envoy-Timestamp'];
        var nonce = headers['x-envoy-nonce'] || headers['X-Envoy-Nonce'];
        if (!signature || !timestamp || !nonce) {
            return false;
        }
        // Prevent replay attacks: reject requests older than 5 minutes
        var reqTime = parseInt(timestamp, 10);
        if (isNaN(reqTime) || Math.abs(Date.now() - reqTime) > 5 * 60 * 1000) {
            return false;
        }
        var expectedSignature = this.computeSignature(timestamp, nonce, payload);
        // Constant-time comparison to prevent timing attacks
        return crypto.timingSafeEqual(Buffer.from(signature, 'hex'), Buffer.from(expectedSignature, 'hex'));
    };
    HMACSignatureProvider.prototype.computeSignature = function (timestamp, nonce, payload) {
        var message = "".concat(timestamp, ".").concat(nonce, ".").concat(payload);
        return crypto
            .createHmac('sha256', this.signingSecret)
            .update(message)
            .digest('hex');
    };
    return HMACSignatureProvider;
}());
exports.HMACSignatureProvider = HMACSignatureProvider;
