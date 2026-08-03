# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-08-03

### Added

- Added `VoiceStreamController`.
- Added optional `discord.py` voice integration.
- Added FFmpeg audio playback for HTTP and HTTPS media URLs.
- Added support for connecting the bot to an empty voice channel.
- Added moving between voice channels.
- Added pause and resume controls.
- Added stop and disconnect controls.
- Added independent voice clients for each Discord guild.
- Added voice-controller tests.

### Notes

- This release provides Discord voice audio playback.
- Discord video Go Live or screen sharing is not implemented by this backend.

## [0.1.0]

### Added

- Initial release.
- Stream queue management.
- Per-guild stream sessions.
- URL validation.
- Media-source resolution.
- Start, pause, resume, skip, and stop controls.
