# API Specification

## Common Requirements

Base URL:

```text
TODO - Requires business confirmation: internal chatbot API base URL
```

Required authentication header for protected APIs:

```http
X-Internal-Service-Token: <internal-service-token>
```

The backend derives `product_id` from the service token. Clients must not be trusted to provide product identity for authorization.

Common error response:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid internal service token.",
    "request_id": "req_01HZX8R2J3C4VT"
  }
}
```

## POST `/chat`

### Purpose

Submits a user message and returns a product-scoped chatbot response.

### Authentication

Required.

### Headers

| Header | Required | Description |
| --- | --- | --- |
| `Content-Type: application/json` | Yes | Request body format |
| `X-Internal-Service-Token` | Yes | Internal product service token |
| `X-Request-Id` | No | Client-provided trace identifier |

### Request JSON

```json
{
  "conversation_id": "conv_01HZX9Y7A6P2",
  "message": "How do I create a quarterly performance report?",
  "user": {
    "id": "u_84721",
    "display_name": "Ananya Rao",
    "department": "Analytics"
  },
  "context": {
    "locale": "en-IN",
    "channel": "web-widget"
  }
}
```

### Response JSON

```json
{
  "conversation_id": "conv_01HZX9Y7A6P2",
  "message_id": "msg_01HZX9Z2J8N5",
  "answer": "You can create a quarterly performance report from the Tensor Reports workspace by selecting Reports > Quarterly Summary and choosing the relevant business unit.",
  "citations": [
    {
      "document_id": "doc_tensor_reporting_guide",
      "title": "Tensor Reporting Guide",
      "source": "tensor/reports/quarterly-summary.md",
      "chunk_index": 4
    }
  ],
  "branding": {
    "widgetTitle": "Tensor Assistant",
    "primaryColor": "#2563EB"
  }
}
```

### HTTP Status Codes

| Status | Meaning |
| --- | --- |
| `200` | Response generated successfully |
| `400` | Invalid request body |
| `401` | Missing or invalid token |
| `403` | Product is inactive |
| `429` | Rate limit exceeded |
| `500` | Unexpected server error |

### Validation Rules

| Field | Rule |
| --- | --- |
| `message` | Required, 1-4000 characters |
| `conversation_id` | Optional, generated if omitted |
| `user.id` | Optional but recommended for audit traces |
| `context.locale` | Optional BCP 47 locale string |

### Possible Errors

| Code | Condition |
| --- | --- |
| `INVALID_REQUEST` | Missing or invalid JSON fields |
| `UNAUTHORIZED` | Token missing or invalid |
| `PRODUCT_DISABLED` | Product is inactive |
| `RETRIEVAL_FAILED` | Qdrant query failed |
| `MODEL_FAILED` | AI generation failed |

### Example curl

```bash
curl -X POST "$CHATBOT_BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Service-Token: TODO - Requires business confirmation" \
  -d '{
    "message": "How do I create a quarterly performance report?",
    "context": { "locale": "en-IN", "channel": "web-widget" }
  }'
```

### Developer Notes

The backend must apply a Qdrant filter where `product_id` equals the product resolved from the token. Never use a client-supplied `product_id` for retrieval.

## POST `/documents/upload`

### Purpose

Uploads or registers documents for ingestion into the product-scoped vector store.

### Authentication

Required.

### Headers

| Header | Required | Description |
| --- | --- | --- |
| `Content-Type: application/json` | Yes | Request body format |
| `X-Internal-Service-Token` | Yes | Internal product service token |

### Request JSON

```json
{
  "document_id": "doc_tensor_forecasting_policy",
  "title": "Tensor Forecasting Policy",
  "source": "tensor/policies/forecasting-policy.md",
  "language": "en",
  "document_type": "policy",
  "content": "Forecasting models in Tensor must be reviewed before production use.",
  "metadata": {
    "owner": "Analytics Platform",
    "classification": "internal"
  }
}
```

### Response JSON

```json
{
  "document_id": "doc_tensor_forecasting_policy",
  "product_id": "tensor",
  "status": "accepted",
  "chunks_queued": 6
}
```

### HTTP Status Codes

| Status | Meaning |
| --- | --- |
| `202` | Document accepted for processing |
| `400` | Invalid request |
| `401` | Unauthorized |
| `403` | Product inactive |
| `409` | Duplicate document conflict |
| `413` | Document too large |

### Validation Rules

| Field | Rule |
| --- | --- |
| `document_id` | Required, stable within product |
| `title` | Required, 1-240 characters |
| `source` | Required, path or URI |
| `language` | Required ISO language code |
| `content` | Required unless using external object reference |
| `document_type` | Required controlled vocabulary |

### Possible Errors

| Code | Condition |
| --- | --- |
| `DOCUMENT_TOO_LARGE` | Content exceeds configured ingestion limit |
| `UNSUPPORTED_DOCUMENT_TYPE` | Document type is not allowed |
| `DUPLICATE_DOCUMENT` | Document exists and overwrite is disabled |

### Example curl

```bash
curl -X POST "$CHATBOT_BASE_URL/documents/upload" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Service-Token: TODO - Requires business confirmation" \
  -d '{
    "document_id": "doc_admissions_fee_policy",
    "title": "Admissions Fee Policy",
    "source": "admissions/policies/fees.md",
    "language": "en",
    "document_type": "policy",
    "content": "Application fee waivers are available for eligible candidates."
  }'
```

### Developer Notes

The ingestion pipeline must stamp the resolved `product_id` onto every vector payload. The client request body does not need to include `product_id`.

## GET `/products`

### Purpose

Lists active internal products and their public widget configuration.

### Authentication

Required for internal administrative clients.

### Headers

| Header | Required | Description |
| --- | --- | --- |
| `X-Internal-Service-Token` | Yes | Internal service token |

### Request JSON

No request body.

### Response JSON

```json
{
  "products": [
    {
      "product_id": "tensor",
      "product_name": "Tensor",
      "is_active": true,
      "branding_config": {
        "widgetTitle": "Tensor Assistant",
        "primaryColor": "#2563EB"
      }
    }
  ]
}
```

### HTTP Status Codes

| Status | Meaning |
| --- | --- |
| `200` | Products returned |
| `401` | Unauthorized |
| `403` | Caller lacks administrative access |

### Validation Rules

No request body is accepted.

### Possible Errors

| Code | Condition |
| --- | --- |
| `UNAUTHORIZED` | Missing or invalid token |
| `FORBIDDEN` | Token does not allow product listing |

### Example curl

```bash
curl "$CHATBOT_BASE_URL/products" \
  -H "X-Internal-Service-Token: TODO - Requires business confirmation"
```

### Developer Notes

Do not return token hashes from this endpoint.

## POST `/products`

### Purpose

Creates an internal product registry entry.

### Authentication

Required for platform administrators.

### Headers

| Header | Required | Description |
| --- | --- | --- |
| `Content-Type: application/json` | Yes | Request body format |
| `X-Internal-Service-Token` | Yes | Platform admin token |

### Request JSON

```json
{
  "product_id": "placement-cell",
  "product_name": "Placement Cell",
  "service_token": "TODO - Requires business confirmation",
  "branding_config": {
    "primaryColor": "#0F766E",
    "accentColor": "#F97316",
    "widgetTitle": "Placement Assistant",
    "welcomeMessage": "Ask about placement drives, eligibility, and interview schedules."
  }
}
```

### Response JSON

```json
{
  "product_id": "placement-cell",
  "product_name": "Placement Cell",
  "is_active": true,
  "created_at": "2026-06-29T09:30:00Z"
}
```

### HTTP Status Codes

| Status | Meaning |
| --- | --- |
| `201` | Product created |
| `400` | Invalid request |
| `401` | Unauthorized |
| `403` | Caller lacks administrative access |
| `409` | Product or token already exists |

### Validation Rules

| Field | Rule |
| --- | --- |
| `product_id` | Lowercase letters, numbers, and hyphens |
| `product_name` | Required |
| `service_token` | Required, minimum 32 characters in production |
| `branding_config` | Required JSON object |

### Possible Errors

| Code | Condition |
| --- | --- |
| `PRODUCT_EXISTS` | Product ID already exists |
| `WEAK_TOKEN` | Token does not meet security policy |
| `INVALID_BRANDING_CONFIG` | Branding JSON fails validation |

### Example curl

```bash
curl -X POST "$CHATBOT_BASE_URL/products" \
  -H "Content-Type: application/json" \
  -H "X-Internal-Service-Token: TODO - Requires business confirmation" \
  -d '{
    "product_id": "website-analyzer",
    "product_name": "Website Analyzer",
    "service_token": "TODO - Requires business confirmation",
    "branding_config": {
      "primaryColor": "#0E7490",
      "accentColor": "#84CC16",
      "widgetTitle": "Website Analyzer Assistant"
    }
  }'
```

### Developer Notes

Hash `service_token` before storage and discard plaintext immediately after creation.

## GET `/health`

### Purpose

Returns service health information for uptime checks and deployment verification.

### Authentication

Not required for basic health. Detailed dependency checks should be restricted to internal networks.

### Headers

No required headers.

### Request JSON

No request body.

### Response JSON

```json
{
  "status": "ok",
  "service": "central-chatbot-backend",
  "version": "1.0.0",
  "dependencies": {
    "postgresql": "ok",
    "qdrant": "ok"
  }
}
```

### HTTP Status Codes

| Status | Meaning |
| --- | --- |
| `200` | Service is healthy |
| `503` | One or more required dependencies are unavailable |

### Validation Rules

No request body is accepted.

### Possible Errors

| Code | Condition |
| --- | --- |
| `DEPENDENCY_UNAVAILABLE` | PostgreSQL or Qdrant check failed |

### Example curl

```bash
curl "$CHATBOT_BASE_URL/health"
```

### Developer Notes

Health checks should avoid expensive operations. Use lightweight database and vector-store probes.
