"use strict";
// packages/chatbot-backend-sdk/src/index.ts
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.HMACSignatureProvider = exports.SDKMiddleware = exports.SDKClient = exports.ChatbotSDK = void 0;
exports.createChatbotSDK = createChatbotSDK;
var sdk_1 = require("./sdk");
/**
 * Factory creator function to instantiate the Chatbot SDK.
 */
function createChatbotSDK(options) {
    return new sdk_1.ChatbotSDK(options);
}
// Export public classes, error interfaces, and typing contracts
var sdk_2 = require("./sdk");
Object.defineProperty(exports, "ChatbotSDK", { enumerable: true, get: function () { return sdk_2.ChatbotSDK; } });
var client_1 = require("./client");
Object.defineProperty(exports, "SDKClient", { enumerable: true, get: function () { return client_1.SDKClient; } });
var middleware_1 = require("./middleware");
Object.defineProperty(exports, "SDKMiddleware", { enumerable: true, get: function () { return middleware_1.SDKMiddleware; } });
var crypto_1 = require("./utils/crypto");
Object.defineProperty(exports, "HMACSignatureProvider", { enumerable: true, get: function () { return crypto_1.HMACSignatureProvider; } });
__exportStar(require("./types"), exports);
__exportStar(require("./errors"), exports);
