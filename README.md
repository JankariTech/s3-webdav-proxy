# S3-WebDAV Proxy

A Docker-based proxy that exposes WebDAV storage as an S3-compatible interface using [rclone](https://rclone.org/).

💰 [PointCab GmbH](https://pointcab-software.com/) is providing finances for this project.

## Features

- **Two modes of operation:**
  - **Per-user mode (`--auth-proxy`)**: Each S3 request uses the client's access token (passed as the S3 access key ID) and a fixed secret key for SigV4 authentication to access their WebDAV backend
  - **Anonymous mode**: Single static WebDAV remote for public access without credentials
- **S3-compatible**: Works with any S3 client (e.g., `mc`)
- **Docker-ready**: Simple containerized deployment
- **Customizable auth-proxy**: Override the auth-proxy script for custom authentication logic

## Purpose

This proxy allows accessing WebDAV backends through the S3 protocol. As a developer of an app that can talk to S3 backends, you can access WebDAV servers through the S3 protocol without having to implement and maintain two protocols in your code.

**Note:** So far we have tested it with [ownCloud](https://github.com/owncloud/ocis) and [Nextcloud](https://github.com/nextcloud/server).

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
docker run --rm -p 8080:8080 \
  -e REMOTE_NAME=<remote-name> \
  -e REMOTE_URL="https://your-webdav-server.com/<webdav-path>" \
  -e REMOTE_VENDOR=<vendor> \
  -e PROXY_ARGS="--auth-proxy --auth-key ,<secret-key> -vv" \
  jankaritech/s3-webdav-proxy
```

The S3-compatible server will be available at `http://localhost:8080`. Access it using an S3 client (e.g., `mc`).

> **Note:** 
> - `<secret-key>` is the **secret key** for SigV4 signature validation (format: `,<secret-key>`).
> - For development/testing with self-signed certificates, add `--no-check-certificate` to `PROXY_ARGS` to disable SSL verification. **Do not use in production** - use a valid certificate instead.
> - If you want to use a WebDAV server running on localhost, add `--network=host` to the docker run command.

## Configuration

### Environment Variables

| Variable          | Required | Description                                                                |
|-------------------|----------|----------------------------------------------------------------------------|
| `REMOTE_NAME`     | Yes      | Name for the rclone remote (e.g., `ocis`)                                  |
| `REMOTE_URL`      | Yes      | WebDAV server URL                                                          |
| `REMOTE_VENDOR`   | Yes      | WebDAV vendor (Tested vendors are nextcloud and owncloud.)                    |
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
docker run --rm -p 8080:8080 \
  -e REMOTE_NAME=<remote-name> \
  -e REMOTE_URL="https://your-server.com/<public-webdav-path>" \
  -e REMOTE_VENDOR=<vendor> \
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
docker run --rm -p 8080:8080 \
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
docker run --rm -p 8080:8080 \
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

## Example: Nextcloud Setup

### Prerequisites

1. Start Nextcloud server (or use your existing Nextcloud instance)

2. Get an access token from Nextcloud:

   **Using app-password**
   - Go to Personal Settings → Security
   - Generate a new app password
   - Use the app password as your bearer token

### Configuration

- `REMOTE_NAME=nextcloud`
- `REMOTE_URL=https://your-nextcloud.com/remote.php/webdav` (for per-user access)
- `REMOTE_VENDOR=nextcloud`

> **Note:** For per-user access, you can use the simpler `/remote.php/webdav` endpoint since authentication is handled by the auth-proxy. For anonymous public access, you must use `/public.php/dav/files/<share-token>/` format since the share token needs to be embedded in the URL.

### Per-User Access Example

```bash
docker run --rm -p 8080:8080 \
  -e REMOTE_NAME=nextcloud \
  -e REMOTE_URL="https://your-nextcloud.com/remote.php/webdav" \
  -e REMOTE_VENDOR=nextcloud \
  -e PROXY_ARGS="--auth-proxy --auth-key ,<secret-key> -vv" \
  jankari/rclone-webdav-proxy
```

```bash
mc alias set myproxy http://localhost:8080 <your-nextcloud-app-password> <secret-key>
mc ls myproxy
```

### Anonymous Public Access Example

1. Create a public share in Nextcloud
2. Use the share token in the URL:

   > **Note:** The share token is the part after `/s/` in your Nextcloud share link.  
   > For example, if your share link is `https://nextcloud.local/index.php/s/sXtwtoMdjcWwk85`,  
   > then your share token is `sXtwtoMdjcWwk85`.  
   > **Note:** For anonymous public access, the share token must be embedded in the URL using the `/public.php/dav/files/<share-token>/` format. This differs from per-user access which can use the simpler `/remote.php/webdav` endpoint.

```bash
docker run --rm -p 8080:8080 \
  -e REMOTE_NAME=nextcloud \
  -e REMOTE_URL="https://your-nextcloud.com/public.php/dav/files/<share-token>/" \
  -e REMOTE_VENDOR=nextcloud \
  jankaritech/s3-webdav-proxy
```

```bash
mc alias set myproxy http://localhost:8080 "" ""
mc ls myproxy
```

## License

MIT
