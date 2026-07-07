# Seed Configuration Templates

## Purpose

This folder stores seed-level templates used by the internal multi-product AI chatbot platform.

## Company Branding Template

`company-branding-schema.json` is the shared branding configuration template for all enterprise products. It mirrors the JSONB object stored in `internal_products.branding_config`.

Products customize values only. They must not rename fields, remove required fields, or introduce product-specific schema variants.

Approved customization examples:

| Product | Allowed Customization |
| --- | --- |
| Tensor | Set `primaryColor`, `widgetTitle`, `launcherLabel`, `welcomeMessage`, `logoUrl`, and related brand values |
| Admissions | Set admissions-specific colors, labels, welcome message, and asset paths |
| HR Portal | Set HR-specific widget copy, logo, and accessible color tokens |
| Website Analyzer | Set product-specific assistant title, launcher label, and preview colors |

Schema changes must be made centrally in `docs/company-branding-schema.md`, reviewed with validation rules, and then reflected in this template.

## Usage

When creating a new product record in `internal_products`, copy the full template object and replace values with approved product branding values.

Required rules:

| Rule | Reason |
| --- | --- |
| Keep every required key present | Frontend widgets and dashboard previews depend on stable field names |
| Use valid enterprise asset paths | Logo and favicon rendering must remain controlled by internal asset hosting |
| Keep service tokens out of branding JSON | Tokens belong to secure token management, not presentation configuration |
| Update `version` when the schema changes | Consumers can detect migration requirements |
| Update `updatedAt` when product branding changes | Audit tooling can identify the latest branding revision |
