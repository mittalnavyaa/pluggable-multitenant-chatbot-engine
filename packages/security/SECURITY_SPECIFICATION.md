# Zero-Trust Cryptographic Verification Specifications

This document outlines the cryptographic handshake protocol and zero-trust verification strategy governing server-to-server calls between the `@envoy-ai/chatbot-backend-sdk` middleware and the core FastAPI RAG Engine.

---

## 1. Interaction Flow Sequence

The client browser never holds private signing keys or signs request headers. The signature is computed and verified exclusively between server-side components.

```
Browser Widget (<envoy-chatbot>)
      │
      │ 1. POST /chat (User Message JSON)
      ▼
Host Server Backend (runs SDK middleware)
      │
      │ 2. Construct Canonical Request
      │ 3. Compute HMAC-SHA256 signature
      │ 4. Inject signature, timestamp, nonce, API-key headers
      ▼
FastAPI Gateway Backend (runs Verification middleware)
      │
      │ 5. Intercept request
      │ 6. Verify clock skew window (<= 5 minutes)
      │ 7. Check if nonce is cached (replay attack prevention)
      │ 8. Re-compute canonical request and verify HMAC
      │ 9. Assert tenant ID matches payload bot workspace
      ▼
Execute Chatbot Query
```

---

## 2. Canonical Request Serialization Rules

To guarantee deterministic signatures across different operating systems, request parameters are serialized using a strict newline-separated sequence:

`HTTP_METHOD\nPATH\nQUERY_PARAMS\nHEADER_PRODUCT_ID\nHEADER_TIMESTAMP\nHEADER_NONCE\nBODY_PAYLOAD`

1. **HTTP_METHOD**: Force-cased to uppercase (e.g. `POST`).
2. **PATH**: Force-cased to lowercase, trailing slashes removed (e.g. `/api/v1/chat/stream`).
3. **QUERY_PARAMS**: Keys sorted alphabetically, URI encoded, joined by `&` (e.g. `a=1&b=2`).
4. **HEADER_PRODUCT_ID**: Trims whitespace. Matches target workspace tenant.
5. **HEADER_TIMESTAMP**: String representation of Unix epoch milliseconds.
6. **HEADER_NONCE**: String unique identifier.
7. **BODY_PAYLOAD**: String representation of JSON request body. Empty string if body is empty.

---

## 3. Cryptographic Signature Generation

- **Algorithm**: HMAC-SHA256.
- **Encoding**: Lowercase hexadecimal string digest.
- **Placement**: Placed inside headers mapping to keys:
  - `X-Envoy-Signature`: The computed hash signature.
  - `X-Envoy-Timestamp`: The timestamp used to compute the signature.
  - `X-Envoy-Nonce`: The nonce string.

---

## 4. Replay Attack & Verification Controls

### Clock Skew Thresholds
- Clock skew tolerance: **5 minutes (300,000 milliseconds)**.
- Timestamps outside this window (either in the past or future) are immediately rejected with `EXPIRED_TIMESTAMP`.

### Nonce Replay Prevention
- Host servers must submit unique nonces.
- Verifying gateways store verified nonces inside memory caches. Duplicate nonces trigger `REPLAY_ATTACK` errors.
- Nonce records are automatically garbage-collected after 10 minutes to prevent resource exhaustion.

---

## 5. Unified Authentication Error Schemas

Standardized structures are returned on verification failures:
- `MISSING_HEADERS`: Inbound request lacks signature headers.
- `INVALID_SIGNATURE`: Cryptographic hash check failed.
- `EXPIRED_TIMESTAMP`: Clock skew threshold crossed.
- `REPLAY_ATTACK`: Nonce has already been processed.

```json
{
  "success": false,
  "error": {
    "code": "INVALID_SIGNATURE",
    "message": "SDK Security Error: Invalid request signature - HMAC signature mismatch.",
    "correlation_id": "req-901-abc",
    "timestamp": "2026-07-09T10:45:00Z",
    "retryable": false
  }
}
```

---

## 6. Audit Logging Specs

All verification states must trigger audit logs:
```
[AUDIT] [2026-07-09T10:45:00Z] Status: FAILED | Action: SIGNATURE_VERIFICATION | ProductID: tenant-omega | Nonce: xyz-123 | Reason: EXPIRED_TIMESTAMP | CorrelationID: req-901-abc
```
Log items include:
- Status: `SUCCESS` or `FAILED`.
- Reason: Detailed cause (e.g. `HMAC_MISMATCH`, `REPLAY_ATTACK`).
- CorrelationID: Trace tracker.
- ProductID: Tenant product workspace ID.

---

## 7. Key Rotation & Management Policy

1. **Environment Separation**: Secrets must be stored in server environments (`CHATBOT_PRODUCT_SECRET`) and never leaked to git.
2. **Transition Keys**: Core engines support validating signatures against two active keys during rotation transitions:
   - `CHATBOT_CURRENT_SECRET`
   - `CHATBOT_PREVIOUS_SECRET`
3. **Revocation**: If a leak occurs, the secret is updated instantly, deprecating the leaked hash and rejecting signatures signed with it.
