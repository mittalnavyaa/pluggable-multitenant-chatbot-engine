# Company Branding Schema

## Purpose

The company branding schema defines the JSONB structure stored in `internal_products.branding_config` for every internal chatbot product.

This platform is an internal multi-product AI chatbot platform. Products such as Tensor, Admissions, Internal Support, HR Portal, Placement Cell, Website Analyzer, and Knowledge Base all belong to the same enterprise. The schema gives each product its own visual identity while keeping widget behavior, validation, and administration consistent.

## Overview

`branding_config` is a PostgreSQL `jsonb` object owned by the `internal_products` table. It stores product-level presentation settings consumed by the chatbot widget, internal dashboard, and product administration flows.

The schema is grouped by responsibility:

| Group | Purpose |
| --- | --- |
| Color | Defines accessible product colors used by the widget and dashboard previews |
| Typography | Defines font family and font weights |
| Widget | Defines customer-facing widget labels and messages |
| Layout | Defines sizing, spacing, radius, and elevation |
| Brand | Defines product logo and favicon URLs |
| Buttons | Defines button shape and style |
| Accessibility | Defines contrast and dark-mode capability |
| Metadata | Defines schema versioning and update tracking |

## Why JSONB Is Used

`jsonb` is used because product branding evolves faster than core product identity fields.

Benefits:

| Benefit | Explanation |
| --- | --- |
| Flexible configuration | New visual properties can be added without a table migration for every UI option |
| Structured storage | PostgreSQL stores parsed JSON, not raw text |
| Query support | Operators such as `->`, `->>`, and `@>` support admin search and reporting |
| Index support | GIN indexes can accelerate JSONB lookups when needed |
| Product isolation | Each product keeps its own complete branding object |
| Backward compatibility | New optional fields can be introduced while older product records continue to work |

## Complete Schema Dictionary

| Name | Datatype | Description | Validation | Default |
| --- | --- | --- | --- | --- |
| `primaryColor` | string | Primary product color used for launcher, primary actions, active navigation, and prominent accents | Required hex color in `#RRGGBB` format; must meet WCAG contrast when paired with `surfaceColor` or `backgroundColor` | `#2563EB` |
| `secondaryColor` | string | Supporting brand color used for secondary UI accents and chart highlights | Required hex color in `#RRGGBB` format | `#0F766E` |
| `accentColor` | string | Attention color used for highlights, focus states, and secondary calls to action | Required hex color in `#RRGGBB` format | `#14B8A6` |
| `backgroundColor` | string | Page or widget background color | Required hex color in `#RRGGBB` format | `#F8FAFC` |
| `surfaceColor` | string | Card, panel, and chat message surface color | Required hex color in `#RRGGBB` format | `#FFFFFF` |
| `textColor` | string | Primary readable text color | Required hex color in `#RRGGBB` format; must provide accessible contrast on `surfaceColor` | `#111827` |
| `mutedTextColor` | string | Secondary text, metadata, captions, and helper text color | Required hex color in `#RRGGBB` format; must remain readable on `surfaceColor` | `#64748B` |
| `successColor` | string | Success, available, completed, and healthy status color | Required hex color in `#RRGGBB` format | `#15803D` |
| `warningColor` | string | Warning, degraded, queued, or attention-needed status color | Required hex color in `#RRGGBB` format | `#B45309` |
| `errorColor` | string | Error, disabled, failed, or blocked status color | Required hex color in `#RRGGBB` format | `#B91C1C` |
| `fontFamily` | string | CSS font-family stack used by the chatbot widget and previews | Required string; must include at least one enterprise-approved fallback such as `Arial`, `Inter`, or `system-ui` | `Inter, Arial, sans-serif` |
| `headingWeight` | number | Font weight used for headings and widget title | Required integer; allowed values: `500`, `600`, `700` | `600` |
| `bodyWeight` | number | Font weight used for chat body text, labels, and supporting copy | Required integer; allowed values: `400`, `500` | `400` |
| `widgetTitle` | string | Header title displayed inside the chatbot widget | Required string; 3-80 characters; trimmed; product-specific | `Enterprise Assistant` |
| `launcherLabel` | string | Accessible label and optional visible label for the launcher button | Required string; 3-60 characters; should identify the product assistant | `Open assistant` |
| `welcomeMessage` | string | First message displayed when the widget opens | Required string; 20-240 characters; no HTML | `Welcome. Ask the assistant for help with this product.` |
| `placeholderText` | string | Input placeholder shown before the user types a message | Required string; 10-100 characters; no HTML | `Type your question...` |
| `borderRadius` | string | Radius used for widget container, cards, and input controls | Required CSS length; allowed units: `px`, `rem`; recommended range: `4px`-`16px` | `8px` |
| `spacing` | string | Base spacing token used by widget layout | Required CSS length; allowed units: `px`, `rem`; recommended range: `8px`-`24px` | `16px` |
| `shadow` | string | CSS box-shadow value for widget panel elevation | Required string; must be an approved token or safe CSS shadow value | `0 16px 40px rgba(15, 23, 42, 0.16)` |
| `maxWidth` | string | Maximum width of the open chatbot widget | Required CSS length; allowed units: `px`, `rem`; recommended range: `360px`-`520px` | `420px` |
| `logoUrl` | string | HTTPS URL for the product logo displayed in dashboard and widget header | Optional string; must be HTTPS URL or approved internal asset path | `/assets/branding/enterprise-assistant.svg` |
| `faviconUrl` | string | HTTPS URL or internal path for browser and embedded product icon use | Optional string; must be HTTPS URL or approved internal asset path | `/assets/branding/favicon.ico` |
| `buttonStyle` | string | Primary button visual treatment | Required enum: `filled`, `outlined`, `tonal` | `filled` |
| `buttonRadius` | string | Radius used specifically for buttons and launcher controls | Required CSS length; allowed units: `px`, `rem`; should not exceed `borderRadius` by more than `8px` | `8px` |
| `contrastMode` | string | Accessibility contrast profile used by the widget | Required enum: `standard`, `high` | `standard` |
| `darkModeSupported` | boolean | Whether the product has a tested dark-mode color set | Required boolean | `false` |
| `version` | string | Branding schema version used by administrative tooling | Required semantic version string | `1.0.0` |
| `updatedAt` | string | ISO 8601 timestamp for the last branding configuration update | Required timestamp with timezone | Current update timestamp |

## Validation Rules

| Area | Rule |
| --- | --- |
| Object type | `branding_config` must be a JSON object, never an array, string, number, boolean, or null |
| Unknown fields | Unknown fields should be ignored by read paths and flagged by administrative validation |
| Hex colors | Color fields must match `^#[0-9A-Fa-f]{6}$` |
| Text fields | Text fields must be trimmed and must not contain HTML, script tags, or template expressions |
| URLs | `logoUrl` and `faviconUrl` must be HTTPS URLs or approved internal asset paths beginning with `/assets/` |
| CSS lengths | Length fields must use approved units: `px` or `rem` |
| Button style | `buttonStyle` must be one of `filled`, `outlined`, or `tonal` |
| Contrast mode | `contrastMode` must be one of `standard` or `high` |
| Font weights | `headingWeight` and `bodyWeight` must use supported numeric weights |
| Metadata | `version` must use semantic versioning and `updatedAt` must be an ISO 8601 timestamp |

## Required Fields

The following fields are required for a product to be considered fully configured:

| Group | Required Fields |
| --- | --- |
| Color | `primaryColor`, `secondaryColor`, `accentColor`, `backgroundColor`, `surfaceColor`, `textColor`, `mutedTextColor`, `successColor`, `warningColor`, `errorColor` |
| Typography | `fontFamily`, `headingWeight`, `bodyWeight` |
| Widget | `widgetTitle`, `launcherLabel`, `welcomeMessage`, `placeholderText` |
| Layout | `borderRadius`, `spacing`, `shadow`, `maxWidth` |
| Buttons | `buttonStyle`, `buttonRadius` |
| Accessibility | `contrastMode`, `darkModeSupported` |
| Metadata | `version`, `updatedAt` |

## Optional Fields

| Field | Reason Optional |
| --- | --- |
| `logoUrl` | Some internal products may use text identity until an approved logo asset is available |
| `faviconUrl` | Embedded widgets may not need product-specific favicon rendering |

Optional fields should still be present in the product configuration when known. Empty strings should not be stored; omit the field or use a validated enterprise asset path.

## Example JSON

```json
{
  "primaryColor": "#0F766E",
  "secondaryColor": "#0369A1",
  "accentColor": "#F59E0B",
  "backgroundColor": "#F8FAFC",
  "surfaceColor": "#FFFFFF",
  "textColor": "#111827",
  "mutedTextColor": "#64748B",
  "successColor": "#15803D",
  "warningColor": "#B45309",
  "errorColor": "#B91C1C",
  "fontFamily": "Inter, Arial, sans-serif",
  "headingWeight": 600,
  "bodyWeight": 400,
  "widgetTitle": "Admissions Help Desk",
  "launcherLabel": "Open Admissions Help Desk",
  "welcomeMessage": "Welcome. I can help with admissions eligibility, application status, required documents, scholarships, and important deadlines.",
  "placeholderText": "Ask about admissions, documents, or deadlines",
  "borderRadius": "8px",
  "spacing": "16px",
  "shadow": "0 16px 40px rgba(15, 23, 42, 0.16)",
  "maxWidth": "420px",
  "logoUrl": "/assets/branding/admissions.svg",
  "faviconUrl": "/assets/branding/admissions.ico",
  "buttonStyle": "filled",
  "buttonRadius": "8px",
  "contrastMode": "standard",
  "darkModeSupported": false,
  "version": "1.0.0",
  "updatedAt": "2026-07-06T09:30:00Z"
}
```

## PostgreSQL JSONB Explanation

`jsonb` stores JSON in a decomposed binary format. PostgreSQL can validate the root type, query individual keys, compare contained objects, and index the field.

Common access patterns:

```sql
SELECT
    product_id,
    product_name,
    branding_config ->> 'widgetTitle' AS widget_title,
    branding_config ->> 'primaryColor' AS primary_color
FROM internal_products
WHERE is_active = true
ORDER BY product_name;
```

```sql
SELECT product_id
FROM internal_products
WHERE branding_config @> '{"darkModeSupported": true}'::jsonb;
```

Recommended table constraint:

```sql
ALTER TABLE internal_products
ADD CONSTRAINT internal_products_branding_config_object_chk
CHECK (jsonb_typeof(branding_config) = 'object');
```

## Integration With `internal_products.branding_config`

`internal_products.branding_config` is the source of truth for product branding.

| Consumer | Usage |
| --- | --- |
| Chatbot widget | Applies colors, typography, widget copy, radius, spacing, logo, and launcher labels |
| Internal dashboard | Displays theme previews and allows authorized users to edit branding values |
| Backend APIs | Return product branding as part of authenticated product context |
| Seed data | Provides initial production-like configuration for all enterprise products |
| Audit tooling | Tracks changes through `updatedAt` and product-level `updated_at` columns |

Backend services should continue to authenticate product access with `service_token_hash`. Plaintext service tokens must never be stored in `branding_config`.

## Future Extensibility

The schema is designed for backward-compatible growth.

Expected future additions:

| Area | Possible Fields |
| --- | --- |
| Dark mode | `darkTheme`, `darkSurfaceColor`, `darkTextColor` |
| Localization | `locale`, `direction`, `localizedMessages` |
| Product channels | `allowedOrigins`, `embedMode`, `launcherPosition` |
| Design tokens | `density`, `inputRadius`, `messageBubbleRadius` |
| Governance | `approvedBy`, `approvalStatus`, `changeTicketId` |

Future fields should be optional first, documented in this file, then enforced once all active products are migrated.

## Best Practices

| Practice | Reason |
| --- | --- |
| Keep schema names stable | Frontend and widget clients consume these keys directly |
| Validate at write time | Prevents broken themes from reaching production widgets |
| Use enterprise asset paths | Keeps logo and favicon delivery under internal control |
| Avoid per-product code branches | Product behavior should be data-driven through `branding_config` |
| Preserve accessible contrast | Ensures internal users can read and operate every widget |
| Version the object | Allows dashboard and widget code to handle migrations safely |
| Store complete objects | Reduces fallback ambiguity across widget, dashboard, and API consumers |
| Audit changes | Branding changes affect production user experience and should be traceable |
