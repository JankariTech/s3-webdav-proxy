# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

- Per-user S3 authentication now requires `S3_SECRET_KEY` instead of
  `--auth-key`, matching rclone 1.75.1's auth-proxy protocol.

### Fixed

- Restore per-user WebDAV access with rclone 1.75.1.

### Security
