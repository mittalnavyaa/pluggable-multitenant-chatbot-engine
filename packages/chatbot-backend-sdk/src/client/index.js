"use strict";
// packages/chatbot-backend-sdk/src/client/index.ts
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.SDKClient = void 0;
var http = require("http");
var https = require("https");
var url_1 = require("url");
var errors_1 = require("../errors");
var SDKClient = /** @class */ (function () {
    function SDKClient(apiBase, apiKey, productId, timeout, retries) {
        if (timeout === void 0) { timeout = 5000; }
        if (retries === void 0) { retries = 3; }
        this.apiBase = apiBase;
        this.apiKey = apiKey;
        this.productId = productId;
        this.timeout = timeout;
        this.retries = retries;
    }
    /**
     * Forwards a chat query to the core FastAPI backend, supporting both JSON and streaming response options.
     */
    SDKClient.prototype.queryChatbot = function (botId_1, prompt_1) {
        return __awaiter(this, arguments, void 0, function (botId, prompt, stream) {
            var payload, targetUrl;
            if (stream === void 0) { stream = false; }
            return __generator(this, function (_a) {
                payload = JSON.stringify({ bot_id: botId, prompt: prompt, stream: stream });
                targetUrl = "".concat(this.apiBase, "/api/v1/chat/stream");
                return [2 /*return*/, this.requestWithRetry('POST', targetUrl, payload, stream)];
            });
        });
    };
    /**
     * Retrieves product branding metadata from core backend.
     */
    SDKClient.prototype.getBranding = function (productId) {
        return __awaiter(this, void 0, void 0, function () {
            var targetUrl;
            return __generator(this, function (_a) {
                targetUrl = "".concat(this.apiBase, "/api/v1/products/").concat(productId);
                return [2 /*return*/, this.requestWithRetry('GET', targetUrl)];
            });
        });
    };
    /**
     * Manually triggers vectorization document synchronization pipelines.
     */
    SDKClient.prototype.syncDocuments = function (botId) {
        return __awaiter(this, void 0, void 0, function () {
            var targetUrl, payload;
            return __generator(this, function (_a) {
                targetUrl = "".concat(this.apiBase, "/api/v1/documents/sync");
                payload = JSON.stringify({ bot_id: botId });
                return [2 /*return*/, this.requestWithRetry('POST', targetUrl, payload)];
            });
        });
    };
    /**
     * Execution wrapper handling request timeouts and transient failures retries.
     */
    SDKClient.prototype.requestWithRetry = function (method_1, targetUrl_1, body_1) {
        return __awaiter(this, arguments, void 0, function (method, targetUrl, body, streamResponse, attempt) {
            var err_1, isTransient, delay_1;
            if (streamResponse === void 0) { streamResponse = false; }
            if (attempt === void 0) { attempt = 1; }
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        _a.trys.push([0, 2, , 5]);
                        return [4 /*yield*/, this.dispatchRequest(method, targetUrl, body, streamResponse)];
                    case 1: return [2 /*return*/, _a.sent()];
                    case 2:
                        err_1 = _a.sent();
                        isTransient = err_1 instanceof errors_1.BackendUnavailableError ||
                            (err_1 instanceof errors_1.SDKNetworkError && err_1.message.includes('Status 5'));
                        if (!(isTransient && attempt < this.retries)) return [3 /*break*/, 4];
                        delay_1 = Math.pow(2, attempt) * 100;
                        console.warn("[envoy-client] Transient error on attempt ".concat(attempt, ". Retrying in ").concat(delay_1, "ms..."));
                        return [4 /*yield*/, new Promise(function (resolve) { return setTimeout(resolve, delay_1); })];
                    case 3:
                        _a.sent();
                        return [2 /*return*/, this.requestWithRetry(method, targetUrl, body, streamResponse, attempt + 1)];
                    case 4: throw err_1;
                    case 5: return [2 /*return*/];
                }
            });
        });
    };
    SDKClient.prototype.dispatchRequest = function (method, targetUrl, body, streamResponse) {
        var _this = this;
        if (streamResponse === void 0) { streamResponse = false; }
        return new Promise(function (resolve, reject) {
            var url = new url_1.URL(targetUrl);
            var isHttps = url.protocol === 'https:';
            var requestLib = isHttps ? https : http;
            var headers = {
                'Content-Type': 'application/json',
                'X-Envoy-API-Key': _this.apiKey,
                'X-Envoy-Product-ID': _this.productId
            };
            if (body) {
                headers['Content-Length'] = Buffer.byteLength(body).toString();
            }
            var options = {
                method: method,
                hostname: url.hostname,
                port: url.port || (isHttps ? 443 : 80),
                path: url.pathname + url.search,
                headers: headers,
                timeout: _this.timeout
            };
            var req = requestLib.request(options, function (res) {
                var status = res.statusCode || 500;
                // In streaming mode, resolve the promise directly with response stream if status is success
                if (streamResponse && status >= 200 && status < 300) {
                    resolve(res);
                    return;
                }
                var responseBody = '';
                res.on('data', function (chunk) {
                    responseBody += chunk;
                });
                res.on('end', function () {
                    if (status < 200 || status >= 300) {
                        reject(new errors_1.SDKNetworkError(targetUrl, status, responseBody));
                        return;
                    }
                    try {
                        var json = JSON.parse(responseBody);
                        resolve({ success: true, data: json });
                    }
                    catch (_a) {
                        resolve({ success: true, data: responseBody });
                    }
                });
            });
            req.on('error', function (err) {
                if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
                    reject(new errors_1.BackendUnavailableError(targetUrl, err.message));
                }
                else {
                    reject(new errors_1.SDKNetworkError(targetUrl, 500, err.message));
                }
            });
            req.on('timeout', function () {
                req.destroy();
                reject(new errors_1.ProxyTimeoutError(targetUrl, _this.timeout));
            });
            if (body) {
                req.write(body);
            }
            req.end();
        });
    };
    return SDKClient;
}());
exports.SDKClient = SDKClient;
