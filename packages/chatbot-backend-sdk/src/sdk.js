"use strict";
// packages/chatbot-backend-sdk/src/sdk.ts
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChatbotSDK = void 0;
var errors_1 = require("./errors");
var client_1 = require("./client");
var middleware_1 = require("./middleware");
var ChatbotSDK = /** @class */ (function () {
    function ChatbotSDK(options) {
        this.options = options;
        this.validateOptions(options);
        this.client = new client_1.SDKClient(options.apiBase, options.apiKey, options.productId, options.timeout || 5000, options.retries || 3);
        this.middleware = new middleware_1.SDKMiddleware(this);
    }
    ChatbotSDK.prototype.validateOptions = function (options) {
        if (!options) {
            throw new errors_1.SDKConfigurationError("options", "must be provided as an options object");
        }
        if (typeof options.apiBase !== "string" || !options.apiBase.trim()) {
            throw new errors_1.SDKConfigurationError("apiBase", "must be a non-empty string URL");
        }
        if (typeof options.apiKey !== "string" || !options.apiKey.trim()) {
            throw new errors_1.SDKConfigurationError("apiKey", "must be a non-empty API key string");
        }
        if (typeof options.productId !== "string" || !options.productId.trim()) {
            throw new errors_1.SDKConfigurationError("productId", "must be a non-empty product tenant ID");
        }
        if (typeof options.signingSecret !== "string" || !options.signingSecret.trim()) {
            throw new errors_1.SDKConfigurationError("signingSecret", "must be a non-empty cryptographic signing secret string");
        }
        if (options.timeout !== undefined && (typeof options.timeout !== "number" || options.timeout <= 0)) {
            throw new errors_1.SDKConfigurationError("timeout", "must be a positive number of milliseconds");
        }
        if (options.retries !== undefined && (typeof options.retries !== "number" || options.retries < 0)) {
            throw new errors_1.SDKConfigurationError("retries", "must be a non-negative number of retry counts");
        }
    };
    /**
     * Return client class for future API calls
     */
    ChatbotSDK.prototype.getClient = function () {
        return this.client;
    };
    /**
     * Return middleware handlers for host frameworks integrations
     */
    ChatbotSDK.prototype.getMiddleware = function () {
        return this.middleware;
    };
    /**
     * Get active SDK configuration options
     */
    ChatbotSDK.prototype.getOptions = function () {
        return this.options;
    };
    return ChatbotSDK;
}());
exports.ChatbotSDK = ChatbotSDK;
