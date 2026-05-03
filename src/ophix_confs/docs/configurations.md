---
title: Configurations
slug: configurations
order: 100
section: Configurations
---

The configurations domain stores named configuration snippets and distributes them verbatim to authorised clients over HTTPS. Unlike credentials (which always contain JSON), configurations are stored as raw text in their native format — YAML, JSON, XML, INI, TOML, `.env`, or plain text — and returned with the appropriate `Content-Type` header.

Content is validated against the chosen format on ingestion. What is stored is what clients receive, byte for byte.

---

## Supported formats

| Format | MIME type | Validation |
| --- | --- | --- |
| `json` | `application/json` | JSON syntax |
| `yaml` | `application/x-yaml` | YAML syntax |
| `xml` | `application/xml` | XML well-formedness |
| `ini` | `text/plain` | Section/key structure (requires at least one section header) |
| `toml` | `application/toml` | TOML syntax |
| `env` | `text/plain` | `KEY=value` line structure |
| `raw` | `text/plain` | None — any content accepted |

Format availability is managed in **Admin → Configuration Formats**. Formats can be disabled to prevent new configurations from being created in that format; existing configurations are unaffected.

The Configuration Formats model is hidden from the admin by default. To show it, set `SHOW_CONFIG_FORMATS_MODEL=true` in the server `.env`.

---

## conf-client

`conf-client` is the Tier 1 command-line client for the Ophix configuration server. Configuration is stored in `.conf.env`.

| Variable | Description |
| --- | --- |
| `CONFSERVER_URL` | Configuration server base URL |
| `CONFSERVER_CA_CERT` | Path to the server CA certificate |
| `CONFSERVER_API_TOKEN` | 64-character hex API token |

### Installation

```bash
pip install ophix-conf-client
```

### Bootstrapping

```bash
# One step
conf-client quickstart https://confserver.internal my-client-name

# Step by step
conf-client set server https://confserver.internal
conf-client download ca-cert
conf-client register my-client-name
```

### Token rotation

```bash
conf-client rotate-token
```

Validates the new token before overwriting `.conf.env`. Safe to run from cron.

### Fetching configurations

```bash
conf-client fetch nginx-config                                    # print to stdout
conf-client fetch nginx-config --format-info                      # also show format and timestamp
conf-client fetch nginx-config --output-file /etc/nginx/conf.d/app.conf   # write to file
conf-client fetch nginx-config --output-file -                    # explicit stdout
```

When `--output-file` is a path, the content is written directly to that file and parent directories are created automatically. `--format-info` prints format and timestamp to stdout as a separate line rather than embedding it in the file.

### Verifying retrieval

```bash
conf-client check --all                      # check all mapped configurations
conf-client check --all --verbose            # show error detail on failure
conf-client check --var NGINX_CONFIG_NAME    # check by env var name
conf-client check --name nginx-config        # check by configuration name
```

### Importing configurations

The `import` command uploads a local file to the server as a named configuration. Supply a name using `--name`, `--env`, or both.

**`--name` only** — import by an explicit name. No `.conf.env` changes.

```bash
conf-client import --name nginx-config --input-file nginx.conf.yaml
```

**`--env` only** — look up the configuration name from an env var already in `.conf.env`. Fails if the var is not set.

```bash
conf-client import --env NGINX_CONFIG_NAME --input-file nginx.conf.yaml
```

**`--name` and `--env` together** — import by the explicit name and write the `VAR=name` mapping to `.conf.env` in one step. If the var is already mapped to a different name, the command fails with an error — edit `.conf.env` manually if you intend to change the mapping.

```bash
conf-client import --name nginx-config --env NGINX_CONFIG_NAME --input-file nginx.conf.yaml
# Mapped NGINX_CONFIG_NAME=nginx-config in .conf.env
```

Add `--overwrite` to update an existing configuration instead of creating a new one:

```bash
conf-client import --name nginx-config --input-file nginx.conf.yaml --overwrite
```

Read from stdin by passing `-` as the input file (format must be explicit):

```bash
cat nginx.conf.yaml | conf-client import --name nginx-config --input-file - --format yaml
```

Extension-to-format inference (when `--format` is omitted): `.yaml`/`.yml` → yaml, `.json` → json, `.xml` → xml, `.ini`/`.cfg` → ini, `.toml` → toml, `.env` → env. All others default to `raw`.

---

## Managing configurations in admin

Configurations and client access are managed through the Django admin:

- **Configurations** — create and edit configurations with syntax-highlighted editor, view linked clients
- **Configuration Formats** — view registered formats, toggle availability
- **Client** detail page — manage which configurations a client can access via the Configurations inline

The content editor switches syntax highlighting automatically when you change the format dropdown. Content is validated against the selected format when you save.

When you link a client to a configuration, the `enabled` checkbox on the link controls whether access is active. The client must also be enabled, and the configuration must be enabled, for retrieval to succeed. Disabled links are shown in italic muted text in the admin list.

---

## Tier 2 usage

Tier 2 clients (scripts and services that consume configurations) import directly from the client library. They do not communicate with the server directly.

```python
from ophix_conf_client import get_config

# Fetch the configuration whose name is stored in the NGINX_CONFIG_NAME env var
nginx_conf = get_config("NGINX_CONFIG_NAME")

# nginx_conf is the raw config string — write it, parse it, pass it on
with open("/etc/nginx/conf.d/app.conf", "w") as f:
    f.write(nginx_conf)
```

`get_config(env_var_name)` reads the configuration name from the named environment variable, fetches the raw content from the server, and returns it as a string. If the env var is not set or the fetch fails, it exits with an error.

The `.conf.env` file maps env var names to configuration names. The server holds the content.

---

## API reference

All requests require `Authorization: Token <api_token>` and must originate from the registered host IP.

### Fetch a configuration

```http
GET /api/configs/<name>/
```

Returns the raw configuration content with the format's `Content-Type`. Response headers include:

```http
Content-Type: application/x-yaml
X-Ophix-Config-Format: yaml
X-Ophix-Config-Updated: 2026-03-23T12:00:00Z
```

### Create a configuration

```http
POST /api/configs/<name>/
Content-Type: application/json
```

```json
{
  "format_name": "yaml",
  "content": "key: value\nother: thing",
  "description": "Optional description"
}
```

Returns 201 Created. Content is validated before storing. The creating client is automatically granted `can_update` and `can_delete`.

### Update a configuration

```http
PUT /api/configs/<name>/
Content-Type: application/json
```

```json
{
  "format_name": "yaml",
  "content": "key: new_value"
}
```

Requires `can_update` on the client-configuration link.

### Delete a configuration

```http
DELETE /api/configs/<name>/
```

Requires `can_delete` on the link **and** `ENABLE_ARTIFACT_DELETE=true` in the server `.env`.

---

## Server settings

These variables are set in the server `.env` file. Run `ophix-manage generate_deploy_config --env` to generate a sample `.env` with all variables and their descriptions.

| Variable | Default | Description |
| --- | --- | --- |
| `SHOW_CONFIG_FORMATS_MODEL` | `False` | Show the Configuration Formats model in the admin navigation. Only needed if you want to add custom formats or inspect/disable built-in ones. |

---

## Access control

Every request is validated through four layers:

1. `Host.enabled` — the host machine is registered and active
2. `Client.enabled` — the specific client process is active
3. `Configuration.enabled` — the configuration itself is active
4. `ClientConfiguration.enabled` — this client has been granted access to this configuration

If any layer fails, the request returns **403 Forbidden**. In production (`AUTH_LEAK_INFO=false`) the response does not distinguish between failure reasons.
