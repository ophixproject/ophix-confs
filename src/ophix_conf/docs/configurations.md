---
title: Configurations
slug: configurations
order: 10
section: Configurations
---

# Configurations

The **Configurations** plugin stores named configuration snippets in a
variety of formats and distributes them verbatim to authorised clients
over HTTPS.

Unlike credentials (which always contain JSON), configurations are
stored as raw text in their native format — YAML, JSON, XML, INI,
TOML, .env, or plain text — and returned to clients with the
appropriate `Content-Type` header.

---

## Supported formats

| Format | MIME type | Validation |
|---|---|---|
| `json` | `application/json` | JSON syntax check |
| `yaml` | `application/x-yaml` | YAML syntax check |
| `xml` | `application/xml` | XML well-formedness check |
| `ini` | `text/plain` | INI section/key check |
| `toml` | `application/toml` | TOML syntax check |
| `env` | `text/plain` | KEY=value line check |
| `raw` | `text/plain` | No validation |

---

## API

### Fetch a configuration

```
GET /api/configs/<n>/
Authorization: Token <api_token>
```

Returns the raw configuration content with the format's `Content-Type`.
Additional headers:

```
X-Ophix-Config-Format: yaml
X-Ophix-Config-Updated: 2026-03-23T12:00:00Z
```

---

### Create a configuration

```
POST /api/configs/<n>/
Authorization: Token <api_token>
Content-Type: application/json

{
    "format": "yaml",
    "content": "key: value\nother: thing",
    "description": "Optional description"
}
```

Content is validated against the format before being stored.
The creating client is automatically granted `can_update` and
`can_delete`.

---

### Update a configuration

```
PUT /api/configs/<n>/
Authorization: Token <api_token>
Content-Type: application/json

{
    "format": "yaml",
    "content": "key: new_value"
}
```

Requires `can_update` on the `ClientConfiguration` join record.

---

### Delete a configuration

```
DELETE /api/configs/<n>/
Authorization: Token <api_token>
```

Requires `can_delete` on the join record **and**
`ENABLE_ARTIFACT_DELETE=true` in the server `.env`.

---

## Access control

All requests are validated through the standard Ophix 4-layer check:

1. `Host.enabled`
2. `Client.enabled`
3. `Configuration.enabled`
4. `ClientConfiguration.enabled` (can_read) + operation-specific flag

---

## Adding a new format

New formats are added by installing an updated version of `ophix-conf`:

```bash
pip install --upgrade ophix-conf
ophix-manage migrate   # applies the new format's data migration
```

The new format's CodeMirror mode file, validator, and database row
are all included in the upgraded package.
