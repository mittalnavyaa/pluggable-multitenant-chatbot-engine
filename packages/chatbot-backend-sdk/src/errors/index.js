"use strict";
// packages/chatbot-backend-sdk/src/errors/index.ts
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.UnauthorizedProxyRequest = exports.ProxyTimeoutError = exports.BackendUnavailableError = exports.InvalidSignatureError = exports.NotImplementedError = exports.SDKAuthenticationError = exports.SDKNetworkError = exports.SDKValidationError = exports.SDKConfigurationError = exports.SDKError = void 0;
var SDKError = /** @class */ (function (_super) {
    __extends(SDKError, _super);
    function SDKError(message) {
        var _this = _super.call(this, message) || this;
        _this.name = _this.constructor.name;
        Error.captureStackTrace(_this, _this.constructor);
        return _this;
    }
    return SDKError;
}(Error));
exports.SDKError = SDKError;
var SDKConfigurationError = /** @class */ (function (_super) {
    __extends(SDKConfigurationError, _super);
    function SDKConfigurationError(paramName, reason) {
        if (reason === void 0) { reason = "is missing or invalid"; }
        return _super.call(this, "SDK Configuration Error: Parameter \"".concat(paramName, "\" ").concat(reason, ".")) || this;
    }
    return SDKConfigurationError;
}(SDKError));
exports.SDKConfigurationError = SDKConfigurationError;
var SDKValidationError = /** @class */ (function (_super) {
    __extends(SDKValidationError, _super);
    function SDKValidationError(message) {
        return _super.call(this, "SDK Validation Error: ".concat(message)) || this;
    }
    return SDKValidationError;
}(SDKError));
exports.SDKValidationError = SDKValidationError;
var SDKNetworkError = /** @class */ (function (_super) {
    __extends(SDKNetworkError, _super);
    function SDKNetworkError(endpoint, status, details) {
        return _super.call(this, "SDK Network Error: Fetch request to ".concat(endpoint, " failed with HTTP Status ").concat(status, ".").concat(details ? " ".concat(details) : "")) || this;
    }
    return SDKNetworkError;
}(SDKError));
exports.SDKNetworkError = SDKNetworkError;
var SDKAuthenticationError = /** @class */ (function (_super) {
    __extends(SDKAuthenticationError, _super);
    function SDKAuthenticationError(reason) {
        if (reason === void 0) { reason = "Invalid credentials or token signing validation failed"; }
        return _super.call(this, "SDK Authentication Error: ".concat(reason, ".")) || this;
    }
    return SDKAuthenticationError;
}(SDKError));
exports.SDKAuthenticationError = SDKAuthenticationError;
var NotImplementedError = /** @class */ (function (_super) {
    __extends(NotImplementedError, _super);
    function NotImplementedError(methodName) {
        return _super.call(this, "SDK Feature Error: The method \"".concat(methodName, "\" is not implemented in this version.")) || this;
    }
    return NotImplementedError;
}(SDKError));
exports.NotImplementedError = NotImplementedError;
var InvalidSignatureError = /** @class */ (function (_super) {
    __extends(InvalidSignatureError, _super);
    function InvalidSignatureError(reason) {
        if (reason === void 0) { reason = "HMAC signature mismatch"; }
        return _super.call(this, "SDK Security Error: Invalid request signature - ".concat(reason, ".")) || this;
    }
    return InvalidSignatureError;
}(SDKError));
exports.InvalidSignatureError = InvalidSignatureError;
var BackendUnavailableError = /** @class */ (function (_super) {
    __extends(BackendUnavailableError, _super);
    function BackendUnavailableError(endpoint, details) {
        return _super.call(this, "SDK Network Error: Central backend at ".concat(endpoint, " is unavailable.").concat(details ? " ".concat(details) : "")) || this;
    }
    return BackendUnavailableError;
}(SDKError));
exports.BackendUnavailableError = BackendUnavailableError;
var ProxyTimeoutError = /** @class */ (function (_super) {
    __extends(ProxyTimeoutError, _super);
    function ProxyTimeoutError(endpoint, timeoutMs) {
        return _super.call(this, "SDK Timeout Error: Request to ".concat(endpoint, " timed out after ").concat(timeoutMs, "ms.")) || this;
    }
    return ProxyTimeoutError;
}(SDKError));
exports.ProxyTimeoutError = ProxyTimeoutError;
var UnauthorizedProxyRequest = /** @class */ (function (_super) {
    __extends(UnauthorizedProxyRequest, _super);
    function UnauthorizedProxyRequest(reason) {
        if (reason === void 0) { reason = "Missing or invalid authorization context"; }
        return _super.call(this, "SDK Access Error: Unauthorized proxy routing request - ".concat(reason, ".")) || this;
    }
    return UnauthorizedProxyRequest;
}(SDKError));
exports.UnauthorizedProxyRequest = UnauthorizedProxyRequest;
