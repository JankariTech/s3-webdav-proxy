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
    # Disable chunked uploads for Nextcloud to avoid issues with /webdav endpoint
    # Nextcloud chunked uploads require /dav/files/USER endpoint instead of /webdav
    if vendor.lower() == "nextcloud":
        o["nextcloud_chunk_size"] = "0"
    json.dump(o, sys.stdout, indent="\t")


if __name__ == "__main__":
    main()