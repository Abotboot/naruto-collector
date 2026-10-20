# Windows releases

`release_info.py` owns the public app identity, version and repository. The app version is independent of the unchanged `naruto-free-v92` bridge. Public clients use HTTPS releases without credentials.

1. Freeze and review source, native hashes and regression evidence. Fully exit Collector before any local replacement.
2. Run `Build EXE.ps1` using the existing `.build-env`. Missing dependencies require explicit setup; the build does not upgrade packages. The build emits a unique clean folder, Windows version resources, a standalone hidden `Naruto Update Helper.exe`, sanitized UTF-8 chat seed and self-excluded SHA256 inventory `app-release.json`.
3. Use `.build-env/Scripts/python.exe -B release_package.py package <clean-runtime> <new-output-directory> --notes <release-notes-file>`. Never package an installed folder. The root ZIP has no enclosing directory. Output contains ZIP, `app-release.json`, `update.json`, `SHA256SUMS.txt`, and `RELEASE-NOTES.md`. Fixed ZIP timestamps/order make identical inputs repeatable. Outputs cannot overwrite an existing bundle.
4. Run `Publish Release.ps1 -Bundle <output>` to validate and obtain a browser-compatible upload bundle. Create a draft named `v<version>` in the configured repository, upload all five files, verify names/sizes, then publish as latest. Alternatively, explicitly run with `-Publish` using an already authenticated local `gh`. Existing version tags/releases are immutable: no clobber. Failed uploads leave a draft for inspection.
5. Independently fetch public latest `update.json` and its ZIP, verify SHA256/size, then test a disposable update and preservation/rollback before accepting local installation.

Do not commit workspace sources, profiles, settings, receipts, histories, cache, learned answers or credentials to the public repository. Publish only reviewed tooling/docs and clean release assets. Existing local banks are preserved by the updater even when the clean ZIP supplies public initial seeds. Publisher credentials stay in the publisher's local authenticated browser or `gh`, never in EXEs/configuration.
