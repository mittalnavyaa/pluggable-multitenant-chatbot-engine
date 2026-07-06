# Qdrant Payload Schema

## Overview

Qdrant stores embedded document chunks for all internal products in a shared collection. Product isolation is enforced by a required `product_id` payload field and a mandatory backend-managed filter on every search request.

## Payload Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `product_id` | `keyword` | Yes | Product scope resolved from the internal service token |
| `document_id` | `keyword` | Yes | Stable identifier for the source document |
| `source` | `keyword` | Yes | Internal path, URI, or system reference for the source content |
| `title` | `text` | Yes | Human-readable title used in citations |
| `language` | `keyword` | Yes | ISO language code such as `en` or `en-IN` |
| `created_at` | `datetime` | Yes | Timestamp when the chunk was indexed |
| `chunk_index` | `integer` | Yes | Zero-based chunk position within the document |
| `document_type` | `keyword` | Yes | Controlled category such as `policy`, `guide`, `faq`, or `procedure` |
| `classification` | `keyword` | Recommended | Data classification such as `internal` or `confidential` |
| `owner` | `keyword` | Recommended | Owning team or department |

## Example Payload JSON

```json
{
  "product_id": "tensor",
  "document_id": "doc_tensor_reporting_guide",
  "source": "tensor/guides/reporting-guide.md",
  "title": "Tensor Reporting Guide",
  "language": "en",
  "created_at": "2026-06-29T09:00:00Z",
  "chunk_index": 4,
  "document_type": "guide",
  "classification": "internal",
  "owner": "Analytics Platform"
}
```

## Payload Filtering

Every search must include the resolved product filter:

```json
{
  "must": [
    {
      "key": "product_id",
      "match": {
        "value": "tensor"
      }
    }
  ]
}
```

Optional filters may be added for language, document type, or classification.

## Why Product ID Isolation Exists

All products share one centralized chatbot backend and vector collection. Without `product_id` filtering, a question from HR Portal could retrieve Admissions or Tensor content. Product isolation protects internal data boundaries and keeps answers relevant to the calling product.

The backend must derive `product_id` from the authenticated service token. It must not trust a user-provided `product_id` for retrieval.

## Example Qdrant Filter Queries

### Product-only Search

```json
{
  "vector": [0.012, -0.481, 0.224],
  "limit": 5,
  "filter": {
    "must": [
      {
        "key": "product_id",
        "match": {
          "value": "hr-portal"
        }
      }
    ]
  }
}
```

### Product and Document Type Search

```json
{
  "vector": [0.044, -0.217, 0.771],
  "limit": 8,
  "filter": {
    "must": [
      {
        "key": "product_id",
        "match": {
          "value": "admissions"
        }
      },
      {
        "key": "document_type",
        "match": {
          "value": "policy"
        }
      }
    ]
  }
}
```

### Product and Language Search

```json
{
  "vector": [0.101, -0.332, 0.456],
  "limit": 5,
  "filter": {
    "must": [
      {
        "key": "product_id",
        "match": {
          "value": "internal-support"
        }
      },
      {
        "key": "language",
        "match": {
          "value": "en"
        }
      }
    ]
  }
}
```

## Payload Indexing Explanation

Payload indexing makes filtered vector search efficient. The `product_id` field should be configured as a tenant-aware keyword index:

```json
{
  "field_name": "product_id",
  "field_schema": {
    "type": "keyword",
    "is_tenant": true,
    "payload_m": 16,
    "m": 0
  }
}
```

## Tenant Configuration Explanation

| Setting | Value | Meaning |
| --- | --- | --- |
| `is_tenant` | `true` | Treats `product_id` as a tenant partition key |
| `payload_m` | `16` | Builds product-specific payload graph connectivity |
| `m` | `0` | Avoids global graph connectivity for the tenant field |

This configuration helps create independent semantic neighborhoods for each product.

## Best Practices

| Practice | Reason |
| --- | --- |
| Always filter by `product_id` | Prevents cross-product retrieval |
| Keep `product_id` immutable | Maintains stable vector ownership |
| Use controlled `document_type` values | Improves filtering and analytics |
| Store source references | Enables transparent citations |
| Use ISO timestamps | Keeps ingestion and audit data consistent |
| Avoid sensitive raw text in payload | Store sensitive content only where required |
| Rebuild payload indexes during migrations | Keeps search behavior predictable |
