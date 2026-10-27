# naruto-collector
Naruto Collector for Windows — releases, automatic update feed, and publishing tools.

Get the complete Windows ZIP from [Releases](https://github.com/Abotboot/naruto-collector/releases/latest). Version 93.1.12 fixes recovery crashing when the game reports idle before its balances load. It waits for protected balances and handles missing persistence replies and malformed CDP startup data through bounded observation. Auto shows the current readiness state and keeps private error-frame diagnostics. Original receipts and earned history stay preserved; reconciliation still requires fresh account/idle/resource proof. Includes direct native heartbeat checks, Wishing Tree/Training recovery, team previews, Auto handoff and All Magatama improvements. See the release notes for limits and verification.

Extract the full ZIP into one folder. Keep `_internal` and `Naruto Update Helper.exe` beside `Naruto Collector.exe`; Python is not required. See [Quick start](QUICKSTART.md) for game/CDP setup and the one-time upgrade from older clients.

Versions 93.0.0 and later can check this repository's latest release on startup or through Help. Finish the current pass and stop Auto before updating. In-app updates preserve profiles, settings, histories, pending receipts and personal answer banks. Unknown gameplay outcomes still require their original evidence.
