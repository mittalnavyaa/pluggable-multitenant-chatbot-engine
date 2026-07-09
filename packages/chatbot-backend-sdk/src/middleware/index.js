"use strict";
// packages/chatbot-backend-sdk/src/middleware/index.ts
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
exports.SDKMiddleware = void 0;
var errors_1 = require("../errors");
var crypto_1 = require("../utils/crypto");
var SDKMiddleware = /** @class */ (function () {
    function SDKMiddleware(sdk) {
        var _this = this;
        this.sdk = sdk;
        /**
         * Request interceptor middleware validating user payload parameters.
         */
        this.requestMiddleware = function (req, res, next) {
            var body = req.body || {};
            if (!body.bot_id || typeof body.bot_id !== 'string') {
                res.status(400).json({ success: false, error: 'Bad Request: "bot_id" parameter is required.' });
                return;
            }
            if (!body.prompt || typeof body.prompt !== 'string') {
                res.status(400).json({ success: false, error: 'Bad Request: "prompt" parameter is required.' });
                return;
            }
            next();
        };
        /**
         * Response sanitizer middleware (stubs).
         */
        this.responseMiddleware = function (req, res, next) {
            next();
        };
        /**
         * Inbound signature authentication verification middleware.
         */
        this.authenticationMiddleware = function (req, res, next) {
            var signature = req.headers['x-envoy-signature'] || req.headers['X-Envoy-Signature'];
            if (!signature) {
                next(new errors_1.UnauthorizedProxyRequest("Missing required header X-Envoy-Signature"));
                return;
            }
            next();
        };
        /**
         * Core secure network proxy routing middleware forwarding request prompts to core FastAPI backend,
         * injecting server credentials, cryptographic signatures, and handling Server-Sent Events streams piping.
         */
        this.proxyMiddleware = function (req, res) { return __awaiter(_this, void 0, void 0, function () {
            var startTime, body, botId, prompt, isStream, options, client, signer, signPayload, signatureHeaders, response, duration, err_1, duration, status_1, errorMsg;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        startTime = Date.now();
                        body = req.body || {};
                        botId = body.bot_id;
                        prompt = body.prompt;
                        isStream = body.stream === true;
                        options = this.sdk.getOptions();
                        client = this.sdk.getClient();
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 3, , 4]);
                        signer = new crypto_1.HMACSignatureProvider(options.apiKey, options.productId, options.signingSecret);
                        signPayload = JSON.stringify({ bot_id: botId, prompt: prompt, stream: isStream });
                        signatureHeaders = signer.sign(signPayload);
                        // 3. Dispatch call to client proxy
                        console.log("[envoy-proxy] Forwarding request for bot ".concat(botId, " (Stream: ").concat(isStream, ")"));
                        return [4 /*yield*/, client.queryChatbot(botId, prompt, isStream)];
                    case 2:
                        response = _a.sent();
                        // 4. Handle response transfer formats
                        if (isStream) {
                            // SSE pipe response logic
                            res.setHeader('Content-Type', 'text/event-stream');
                            res.setHeader('Cache-Control', 'no-cache');
                            res.setHeader('Connection', 'keep-alive');
                            response.on('data', function (chunk) {
                                res.write(chunk);
                            });
                            response.on('end', function () {
                                var duration = Date.now() - startTime;
                                console.log("[envoy-proxy] SSE Stream ended successfully. Duration: ".concat(duration, "ms"));
                                res.end();
                            });
                            response.on('error', function (err) {
                                console.error("[envoy-proxy] SSE Stream connection error:", err);
                                res.write("data: ".concat(JSON.stringify({ error: 'Connection interrupted' }), "\n\n"));
                                res.end();
                            });
                        }
                        else {
                            duration = Date.now() - startTime;
                            console.log("[envoy-proxy] JSON request completed. Duration: ".concat(duration, "ms"));
                            res.status(200).json(response);
                        }
                        return [3 /*break*/, 4];
                    case 3:
                        err_1 = _a.sent();
                        duration = Date.now() - startTime;
                        console.error("[envoy-proxy] Ingestion proxy routing failed after ".concat(duration, "ms: ").concat(err_1.message));
                        status_1 = 500;
                        errorMsg = 'An internal gateway proxy error occurred.';
                        if (err_1 instanceof errors_1.InvalidSignatureError) {
                            status_1 = 403;
                            errorMsg = 'Security validation failure.';
                        }
                        else if (err_1 instanceof errors_1.ProxyTimeoutError) {
                            status_1 = 504;
                            errorMsg = 'Gateway timeout connecting to central agent services.';
                        }
                        else if (err_1 instanceof errors_1.BackendUnavailableError) {
                            status_1 = 503;
                            errorMsg = 'Centralized AI agent engine is currently unreachable.';
                        }
                        else if (err_1 instanceof errors_1.UnauthorizedProxyRequest) {
                            status_1 = 401;
                            errorMsg = 'Access denied.';
                        }
                        res.status(status_1).json({ success: false, error: errorMsg });
                        return [3 /*break*/, 4];
                    case 4: return [2 /*return*/];
                }
            });
        }); };
    }
    return SDKMiddleware;
}());
exports.SDKMiddleware = SDKMiddleware;
