# Release Plan

## Versioning

[Semantic Versioning](https://semver.org/) with `v` prefix: `v{major}.{minor}.{patch}` (e.g., `v1.2.3`).

---

## When to Release

| Trigger                                                | Type       |
| -------------------------------------------------------| -----------|
| Dependabot rclone version bump (e.g., 1.74.2 → 1.74.3) | Patch      |
| New feature/improvement merged to `main`               | Minor      |
| Breaking change merged                                 | Major      |
| Security fix needs immediate shipping                  | Patch ASAP |

---

## Release Process

### Prerequisites

- All changes merged to `main`, CI passing.

### 1. Prepare release

Add new version and date in CHANGELOG.md.

Example:

```markdown
## [Unreleased]

## [1.2.3] - 2024-06-20
```

Commit the changes to main branch.

### 2. Release

1. Go to https://github.com/JankariTech/s3-webdav-proxy/releases/new
2. **Create new tag** on release: always use `v` prefix (e.g., `v1.2.3`)
3. Paste your `CHANGELOG.md` section as the release notes
4. Publish

### 3. Verify Docker image

Verify a new tag is created on Docker Hub: [`jankaritech/s3-webdav-proxy`](https://hub.docker.com/r/jankaritech/s3-webdav-proxy).
