#!/usr/bin/env python3
"""
A proxy for rclone serve s3
"""

import sys
import json
import os


def main():
    i = json.load(sys.stdin)
    url = os.getenv("REMOTE_URL")
    vendor = os.getenv("REMOTE_VENDOR")
    secret = os.getenv("S3_SECRET_KEY")
    if not url:
        print("REMOTE_URL is not set", file=sys.stderr)
        sys.exit(1)
    if not vendor:
        print("REMOTE_VENDOR is not set", file=sys.stderr)
        sys.exit(1)
    if not secret:
        print("S3_SECRET_KEY is not set", file=sys.stderr)
        sys.exit(1)
    access_key = i.get("user")
    if not isinstance(access_key, str) or not access_key:
        print("S3 access key ID is missing or invalid", file=sys.stderr)
        sys.exit(1)
    o = {
        "type": "webdav",
        "_root": "",
        "_secret_access_key": secret,
        "bearer_token": access_key,
        "url": url,
        "vendor": vendor,
    }
    # Disable chunked uploads for Nextcloud to avoid issues with /webdav endpoint
    # Nextcloud chunked uploads require /dav/files/USER endpoint instead of /webdav
    if vendor.lower() == "nextcloud":
        o["nextcloud_chunk_size"] = "0"
    json.dump(o, sys.stdout, indent="\t")


if __name__ == "__main__":
    main()