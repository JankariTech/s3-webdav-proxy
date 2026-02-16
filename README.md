# S3-WebDAV Proxy

A Docker-based proxy that exposes WebDAV storage as an S3-compatible interface using [rclone](https://rclone.org/).

## Features

- **Two modes of operation:**
  - **Per-user mode (`--auth-proxy`)**: Each S3 request uses the client's access token (passed as the S3 access key ID) and a fixed secret key for SigV4 authentication to access their WebDAV backend
  - **Anonymous mode**: Single static WebDAV remote for public access without credentials
- **S3-compatible**: Works with any S3 client (e.g., `mc`)
- **Docker-ready**: Simple containerized deployment
- **Customizable auth-proxy**: Override the auth-proxy script for custom authentication logic

## Purpose

This proxy allows accessing WebDAV backends through the S3 protocol. As a developer of an app that can talk to S3 backends, you can access WebDAV servers through the S3 protocol without having to implement and maintain two protocols in your code.

## How It Works

The proxy is based on [rclone](https://rclone.org/), a powerful tool for managing files on cloud storage. Rclone can serve storage over various protocols, including S3.

The key innovation is handling per-user authentication: each S3 request uses the client's access token (passed as the S3 access key ID) as a Bearer token to authenticate against the WebDAV server. This allows accessing data from different WebDAV users through the S3 protocol.

## Quick Start

### Build the image

```bash
docker build -t jankaritech/s3-webdav-proxy .
```

### Run the container

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=<remote-name> \
  -e REMOTE_URL="https://your-webdav-server.com/<webdav-path>" \
  -e REMOTE_VENDOR=<vendor> \
  -e PROXY_ARGS="--auth-proxy --auth-key ,<secret-key> --no-check-certificate -vv" \
  jankaritech/s3-webdav-proxy
```

The S3-compatible server will be available at `http://localhost:8080`. Access it using an S3 client (e.g., `mc`).

> **Note:** 
> - `<secret-key>` is the **secret key** for SigV4 signature validation (format: `,<secret-key>`).
> - `--no-check-certificate` disables SSL verification. **Do not use in production** - use a valid certificate instead.

## Configuration

### Environment Variables

| Variable          | Required | Description                                                                |
|-------------------|----------|----------------------------------------------------------------------------|
| `REMOTE_NAME`     | Yes      | Name for the rclone remote (e.g., `ocis`)                                  |
| `REMOTE_URL`      | Yes      | WebDAV server URL                                                          |
| `REMOTE_VENDOR`   | Yes      | WebDAV vendor (`owncloud`, `nextcloud`, `webdav`, etc.)                    |
| `PROXY_ARGS`      | No       | Additional rclone arguments                                                |
| `AUTH_PROXY_PATH` | No       | Path to custom auth-proxy script (default: `/usr/local/bin/auth-proxy.py`) |

### PROXY_ARGS Options

Common rclone options for `serve s3`:

| Option                                | Description                                                                                                                                         |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `--auth-proxy <path>`                 | Enable per-user authentication (see modes below)                                                                                                    |
| `--auth-key <access-key-id>,<secret>` | Validate SigV4 signatures with fixed secret (wildcard access key)                                                                                   |
| `--no-check-certificate`              | Disable SSL certificate verification                                                                                                                |
| `-vv`                                 | Verbose logging (debug level)                                                                                                                       |
| `--vfs-cache-max-age`                 | Max time since last access of objects in the cache (default 1h0m0s)                                                                                 |
| `--vfs-cache-max-size`                | Max total size of objects in the cache (default off)                                                                                                |
| `--vfs-cache-mode`                    | Cache mode off\|minimal\|writes\|full (default off)                                                                                                 |
| `--vfs-cache-poll-interval`           | Interval to poll the cache for stale objects (default 1m0s)                                                                                         |
| `--vfs-case-insensitive`              | If a file name not found, find a case insensitive match                                                                                             |
| `--vfs-disk-space-total-size`         | Specify the total space of disk (default off)                                                                                                       |
| `--vfs-fast-fingerprint`              | Use fast (less accurate) fingerprints for change detection                                                                                          |
| `--vfs-read-ahead`                    | Extra read ahead over `--buffer-size` when using cache-mode full                                                                                    |
| `--vfs-read-chunk-size`               | Read the source objects in chunks (default 128Mi)                                                                                                   |
| `--vfs-read-chunk-size-limit`         | If greater than `--vfs-read-chunk-size`, double the chunk size after each chunk read, until the limit is reached ('off' is unlimited) (default off) |
| `--vfs-read-wait`                     | Time to wait for in-sequence read before seeking (default 20ms)                                                                                     |
| `--vfs-used-is-size`                  | rclone size Use the rclone size algorithm for Used size                                                                                             |
| `--vfs-write-back`                    | Time to writeback files after last use when using cache (default 5s)                                                                                |
| `--vfs-write-wait`                    | Time to wait for in-sequence write before giving error (default 1s)                                                                                 |

## Usage Modes

### Per-User Mode (Private Access)

Use `--auth-proxy` to enable per-request authentication. Each S3 client uses their own credentials to access their WebDAV storage.

**1. Start the proxy:**

See [Quick Start](#quick-start) for the docker command.

**2. Configure S3 client (MinIO Client - `mc`):**

```bash
mc alias set myproxy http://localhost:8080 <access-token> <secret-key>
```

- `<access-token>`: Your WebDAV access token
- `<secret-key>`: The secret key (must match the value specified in `--auth-key ,<secret-key>`)

**3. Access your files:**

```bash
mc ls myproxy
```

### Anonymous Mode (Public Access)

Omit `--auth-proxy` to enable anonymous access to a single static WebDAV remote.

**1. Start the proxy:**

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=<remote-name> \
  -e REMOTE_URL="https://your-server.com/<public-webdav-path>" \
  -e REMOTE_VENDOR=<vendor> \
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
  -e REMOTE_NAME=<remote-name> \
  -e REMOTE_URL="https://your-server.com/<webdav-path>" \
  -e REMOTE_VENDOR=<vendor> \
  -e PROXY_ARGS="--auth-proxy --auth-key ,<secret-key>" \
  -v /path/to/custom-auth-proxy.py:/usr/local/bin/auth-proxy.py \
  jankaritech/s3-webdav-proxy
```

### Option 2: Environment Variable

Use a custom path with `AUTH_PROXY_PATH`:

```bash
docker run --rm --network=host \
  -e REMOTE_NAME=<remote-name> \
  -e REMOTE_URL="https://your-server.com/<webdav-path>" \
  -e REMOTE_VENDOR=<vendor> \
  -e PROXY_ARGS="--auth-proxy --auth-key ,<secret-key>" \
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

See [docker/auth-proxy.py](docker/auth-proxy.py) for the complete example implementation.

## Example: OwnCloud OCIS Setup

### Prerequisites

1. Start OCIS server (ocis binary is used here for demonstration, but you can use your own OCIS setup):
   ```bash
   OCIS_LOG_LEVEL=debug IDM_CREATE_DEMO_USERS=true \
   OCIS_INSECURE=true ./ocis/bin/ocis server
   ```

2. Get an access token from OCIS:

   **Option A: Using browser (simplest)**
   - Log in to OCIS web interface with your credentials
   - Open browser DevTools (F12) → Network tab
   - Make any request to OCIS
   - Find the request with `Authorization: Bearer <token>` header
   - Copy the bearer token

   **Option B: Using app-password (Nextcloud only)**
   - Go to Personal Settings → Security
   - Generate a new app password
   - Use the app password as your bearer token

   **Option C: Using oauth2 (advanced)**
   - Install oauth2 app in OCIS
   - Create oauth2 client with redirect URL `http://localhost:9876/`
   - Create a JSON file `oauth.json` with the client credentials:
     ```json
     {
       "installed": {
         "client_id": "<client-id-copied-from-oauth2-app>",
         "auth_uri": "<server-root>/index.php/apps/oauth2/authorize",
         "token_uri": "<server-root>/index.php/apps/oauth2/api/v1/token",
         "client_secret": "<client-secret-copied-from-oauth2-app>",
         "redirect_uris": ["http://localhost:9876"]
       }
     }
     ```
   - Use [oauth2l](https://github.com/google/oauth2l) to fetch token:
     ```bash
     ./oauth2l fetch --credentials oauth.json --scope all --refresh --output_format bare
     ```

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

## License

MIT
