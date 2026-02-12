# S3-WebDAV Proxy

A Docker-based proxy that exposes WebDAV storage as an S3-compatible interface using [rclone](https://rclone.org/).

## Features

- **Two modes of operation:**
  - **Per-user mode (`--auth-proxy`)**: Each S3 request uses the client's credentials to access their own WebDAV backend
  - **Anonymous mode**: Single static WebDAV remote for public access without credentials
- **S3-compatible**: Works with any S3 client (e.g., `mc`)
- **Docker-ready**: Simple containerized deployment
- **Customizable auth-proxy**: Override the auth-proxy script for custom authentication logic

## Quick Start

### Build the image

```bash
docker build -t jankaritech/s3-webdav-proxy .
```

### Run the container

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=ocis \
  -e REMOTE_URL="https://your-webdav-server.com/remote.php/webdav" \
  -e REMOTE_VENDOR=owncloud \
  -e PROXY_ARGS="--auth-proxy --auth-key ,12345678 --no-check-certificate -vv" \
  jankaritech/s3-webdav-proxy
```

The S3-compatible server will be available at `http://localhost:8080`. Access it using an S3 client (e.g., `mc`).

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `REMOTE_NAME` | Yes | Name for the rclone remote (e.g., `ocis`) |
| `REMOTE_URL` | Yes | WebDAV server URL |
| `REMOTE_VENDOR` | Yes | WebDAV vendor (`owncloud`, `nextcloud`, `webdav`, etc.) |
| `PROXY_ARGS` | No | Additional rclone arguments |
| `AUTH_PROXY_PATH` | No | Path to custom auth-proxy script (default: `/usr/local/bin/auth-proxy.py`) |

### PROXY_ARGS Options

Common rclone options for `serve s3`:

| Option | Description |
|--------|-------------|
| `--auth-proxy <path>` | Enable per-user authentication (see modes below) |
| `--auth-key <access-key-id>,<secret>` | Validate SigV4 signatures with fixed secret (wildcard access key) |
| `--no-check-certificate` | Disable SSL certificate verification |
| `-vv` | Verbose logging (debug level) |

## Usage Modes

### Per-User Mode (Private Access)

Use `--auth-proxy` to enable per-request authentication. Each S3 client uses their own credentials to access their WebDAV storage.

**1. Start the proxy:**

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=ocis \
  -e REMOTE_URL="https://your-server.com/remote.php/webdav" \
  -e REMOTE_VENDOR=owncloud \
  -e PROXY_ARGS="--auth-proxy --auth-key ,12345678 --no-check-certificate" \
  jankaritech/s3-webdav-proxy
```

**2. Configure S3 client (MinIO Client - `mc`):**

```bash
mc alias set myproxy http://localhost:8080 <access-token> 12345678
```

- `<access-token>`: Your WebDAV/OCIS access token
- `12345678`: The access key ID (matches `--auth-key` prefix)

**3. Access your files:**

```bash
mc ls myproxy
```

### Anonymous Mode (Public Access)

Omit `--auth-proxy` to enable anonymous access to a single static WebDAV remote.

**1. Start the proxy:**

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=ocis \
  -e REMOTE_URL="https://your-server.com/dav/public-files/<unique-id>" \
  -e REMOTE_VENDOR=owncloud \
  -e PROXY_ARGS="--no-check-certificate" \
  jankaritech/s3-webdav-proxy
```

**2. Configure S3 client with empty credentials:**

```bash
mc alias set myproxy http://localhost:8080 "" ""
```

**3. Access public files:**

```bash
mc ls myproxy
```

## Custom Auth-Proxy Script

The auth-proxy script enables dynamic backend configuration per request. You can customize it in two ways:

### Option 1: Volume Mount

Mount your custom script over the bundled one:

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=ocis \
  -e REMOTE_URL="https://your-server.com/remote.php/webdav" \
  -e REMOTE_VENDOR=owncloud \
  -e PROXY_ARGS="--auth-proxy --auth-key ,12345678" \
  -v /path/to/custom-auth-proxy.py:/usr/local/bin/auth-proxy.py \
  jankaritech/s3-webdav-proxy
```

### Option 2: Environment Variable

Use a custom path with `AUTH_PROXY_PATH`:

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=ocis \
  -e REMOTE_URL="https://your-server.com/remote.php/webdav" \
  -e REMOTE_VENDOR=owncloud \
  -e PROXY_ARGS="--auth-proxy --auth-key ,12345678" \
  -e AUTH_PROXY_PATH="/my/custom/script.py" \
  -v /my/custom/script.py:/my/custom/script.py \
  jankaritech/s3-webdav-proxy
```

### Auth-Proxy Protocol

The auth-proxy script must:

1. **Read from stdin**: JSON with user credentials
   ```json
   {"pass": "<bearer_token>", "user": "<access-key-id>"}
   ```

2. **Write to stdout**: JSON with WebDAV backend config
   ```json
   {
     "type": "webdav",
     "_root": "",
     "bearer_token": "<bearer_token>",
     "url": "https://server.com/remote.php/webdav",
     "vendor": "owncloud"
   }
   ```

Example implementation (`auth-proxy.py`):

```python
#!/usr/bin/env python3
import sys
import json
import os

def main():
    i = json.load(sys.stdin)
    url = os.getenv("REMOTE_URL")
    vendor = os.getenv("REMOTE_VENDOR")
    if not url:
        print("REMOTE_URL is not set", file=sys.stderr)
        sys.exit(1)
    if not vendor:
        print("REMOTE_VENDOR is not set", file=sys.stderr)
        sys.exit(1)
    o = {
        "type": "webdav",
        "_root": "",
        "bearer_token": i["pass"],
        "url": url,
        "vendor": vendor,
    }
    json.dump(o, sys.stdout, indent="\t")

if __name__ == "__main__":
    main()
```

## Example: OwnCloud OCIS Setup

### Prerequisites

1. Start OCIS server (ocis binary is used here for demonstration, but you can use your own OCIS setup):
   ```bash
   OCIS_LOG_LEVEL=debug PROXY_ENABLE_BASIC_AUTH=true \
   IDM_CREATE_DEMO_USERS=true OCIS_INSECURE=true ./ocis/bin/ocis server
   ```

2. Get an access token from OCIS (Follow [this instruction](https://github.com/jankariTech/rclone?tab=readme-ov-file#3-obtain-a-bearer-token-from-the-webdav-server) to get token or you can just get access token from network tab in browser dev tools when you log in to OCIS web interface)

### Per-User Access

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=ocis \
  -e REMOTE_URL="https://localhost:9200/remote.php/webdav" \
  -e REMOTE_VENDOR=owncloud \
  -e PROXY_ARGS="--auth-proxy --auth-key ,12345678 --no-check-certificate -vv" \
  jankaritech/s3-webdav-proxy
```

```bash
mc alias set myproxy http://localhost:8080 <your-ocis-access-token> 12345678
mc ls myproxy
```

### Anonymous Public Access

1. Create a public link in OCIS
2. Use the unique ID from the public link:

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=ocis \
  -e REMOTE_URL="https://localhost:9200/dav/public-files/A1b2C3d4E5f6G7h8I9j0" \
  -e REMOTE_VENDOR=owncloud \
  -e PROXY_ARGS="--no-check-certificate" \
  jankaritech/s3-webdav-proxy
```

```bash
mc alias set myproxy http://localhost:8080 "" ""
mc ls myproxy
```

> [!INFORMATION]
> More details can be found [here](https://github.com/jankariTech/rclone?tab=readme-ov-file#3-obtain-a-bearer-token-from-the-webdav-server)

## License

MIT
