# @envoy/security

Centralized package providing server-to-server zero-trust cryptographic signature generation and request handshakes verification.

---

## Folders

- `src/canonical-request/` — Normalizes incoming HTTP request details into deterministic byte sequences.
- `src/signing/` — Builds standard HMAC-SHA256 signature digests.
- `src/verification/` — Verifies signatures, time windows, and replay prevention nonces.
