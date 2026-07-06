  # Testing Guide

  ## Overview

  This guide describes how developers can verify the Internal Multi-Product AI Chatbot Platform locally or in a shared development environment.

  Testing goals:

  | Goal | Description |
  | --- | --- |
  | Seed PostgreSQL | Load product registry records |
  | Import vectors | Load Qdrant payloads and embeddings |
  | Run backend | Start central chatbot API |
  | Run frontend | Start embeddable widget |
  | Verify authentication | Confirm token validation behavior |
  | Verify isolation | Confirm products cannot retrieve other products' content |

  ## 1. Seed Database

  Load product records from:

  ```text
  seed/products.json
  ```

  Expected result:

  | Product ID | Expected State |
  | --- | --- |
  | `tensor` | Active |
  | `admissions` | Active |
  | `internal-support` | Active |
  | `hr-portal` | Active |
  | `placement-cell` | Active |
  | `website-analyzer` | Active |
  | `knowledge-base` | Active |

  Verification SQL:

  ```sql
  SELECT product_id, product_name, is_active
  FROM internal_products
  ORDER BY product_id;
  ```

  Expected output includes seven active products.

  ## 2. Import Vectors

  Use:

  ```text
  seed/sample_payloads.json
  ```

  Each payload must include:

  | Field | Required |
  | --- | --- |
  | `product_id` | Yes |
  | `document_id` | Yes |
  | `source` | Yes |
  | `title` | Yes |
  | `language` | Yes |
  | `chunk_index` | Yes |
  | `document_type` | Yes |

  Before importing, configure the `product_id` payload index:

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

  ## 3. Run Backend

  Start the backend using the repository's runtime command. Required environment variables typically include:

  ```text
  DATABASE_URL=postgresql://...
  QDRANT_URL=http://localhost:6333
  QDRANT_COLLECTION=internal_chatbot_documents
  MODEL_PROVIDER_API_KEY=...
  TOKEN_HASH_SECRET=...
  ```

  Expected output:

  ```text
  central-chatbot-backend listening
  postgresql: ok
  qdrant: ok
  ```

  ## 4. Run Frontend

  Start the frontend widget development server using the repository's frontend command.

  Expected behavior:

  | Check | Expected Result |
  | --- | --- |
  | Widget loads | Chat interface is visible |
  | Theme loads | Product colors and widget title are applied |
  | Chat request sends | Backend receives `X-Internal-Service-Token` |

  ## 5. Verify Authentication

  ### Valid Token

  ```bash
  curl -X POST "http://localhost:8080/chat" \
    -H "Content-Type: application/json" \
    -H "X-Internal-Service-Token: TODO - Requires business confirmation" \
    -d '{ "message": "How do I create a report?" }'
  ```

  Expected status:

  ```text
  200 OK
  ```

  ### Missing Token

  ```bash
  curl -X POST "http://localhost:8080/chat" \
    -H "Content-Type: application/json" \
    -d '{ "message": "How do I create a report?" }'
  ```

  Expected status:

  ```text
  401 Unauthorized
  ```

  Expected error:

  ```json
  {
    "error": {
      "code": "UNAUTHORIZED",
      "message": "Missing internal service token."
    }
  }
  ```

  ## 6. Verify Product Isolation

  ### Tensor Query

  Request:

  ```bash
  curl -X POST "http://localhost:8080/chat" \
    -H "Content-Type: application/json" \
    -H "X-Internal-Service-Token: TODO - Requires business confirmation" \
    -d '{ "message": "Where can I find forecasting model review guidance?" }'
  ```

  Expected citations:

  ```text
  Only documents with product_id = tensor
  ```

  ### HR Query

  Request:

  ```bash
  curl -X POST "http://localhost:8080/chat" \
    -H "Content-Type: application/json" \
    -H "X-Internal-Service-Token: TODO - Requires business confirmation" \
    -d '{ "message": "How many casual leaves are available?" }'
  ```

  Expected citations:

  ```text
  Only documents with product_id = hr-portal
  ```

  ### Negative Isolation Test

  Ask Tensor a question that only appears in HR documents.

  Expected result:

  | Condition | Expected Behavior |
  | --- | --- |
  | No Tensor source matches | Backend should answer with limited confidence or no matching source |
  | HR source exists | Must not appear in Tensor response |

  ## 7. Expected Outputs

  | Test | Expected Result |
  | --- | --- |
  | `/health` | `200` with PostgreSQL and Qdrant status |
  | Valid `/chat` | `200` with answer and product-scoped citations |
  | Invalid token | `401` |
  | Inactive product | `403` |
  | Cross-product retrieval attempt | No citations from other products |
  | Document upload | `202` and chunks queued |

  ## Common Troubleshooting

  | Symptom | Likely Cause | Resolution |
  | --- | --- | --- |
  | `401 Unauthorized` for valid-looking token | Seed hash does not match runtime hashing | Regenerate token hash using the backend hashing utility |
  | Empty citations | Vectors not imported or wrong collection name | Verify Qdrant collection and payloads |
  | Cross-product citations | Missing `product_id` filter | Inspect retrieval query builder |
  | Slow searches | Missing payload index | Create tenant-aware `product_id` payload index |
  | Branding missing | `branding_config` empty or invalid | Validate PostgreSQL JSONB data |
  | `/health` returns `503` | Dependency unavailable | Check PostgreSQL and Qdrant connectivity |
