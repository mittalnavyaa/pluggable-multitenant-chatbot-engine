# Prompt Behavior Examples

## Repeated Headers

Input:

```text
Employee Handbook
Page 1
Leave Policy
Employees may request leave through the HR Portal.
Employee Handbook
Page 2
Managers approve leave requests.
```

Expected Markdown:

```markdown
# Leave Policy

Employees may request leave through the HR Portal.

Managers approve leave requests.
```

## OCR Noise

Input:

```text
P0l!cy ### Leave Entitlement
Employees receive 12 casual leave days per year.
```

Expected Markdown:

```markdown
# Leave Entitlement

Employees receive 12 casual leave days per year.
```
