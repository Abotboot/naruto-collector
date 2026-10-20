# Naruto Collector for Windows

Download the Windows ZIP from this repository's latest release. Extract the whole ZIP into a normal writable folder, then open **Naruto Collector.exe**. Keep the `_internal` folder and update helper beside it.

This is the first version with built-in updates. Install it once manually; later releases can be offered automatically at startup. **Help → Check for updates** checks immediately. Updates show release notes and offer Install, Later, or Skip this version. Finish the current pass and stop Auto before installing. The app closes, updates, and restarts.

Existing profiles, settings, reward history, pending receipts, and local answer banks are preserved during in-app updates. An update does not clear an unresolved gameplay receipt without verification.

For the one-time upgrade from an older manual installation, stop Auto and close Collector first. Back up the old folder. Extract the new ZIP into a separate folder, then copy your existing `profiles` folder, `ui-settings.json`, `chat-answers.json`, `quiz-reviewed.json`, and personal history/log files into the new folder before opening it. Keep the new EXEs and `_internal`; do not copy the old runtime over them. Do not replace your learned answer banks with the ZIP's starter banks.

**Help** also provides About, Open data folder, and Copy diagnostics. Diagnostics contain only application/platform/update state; they do not include account records or learned answers.

Publishers: see [RELEASING.md](RELEASING.md). Friends do not need GitHub accounts, tokens, Python, or administrator access.
