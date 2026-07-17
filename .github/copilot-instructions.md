
# instructions

## overview
We're creating userscripts for the **ScriptCat** userscript manager (migrated from Violentmonkey).
Userscripts are JavaScript programs that run in the browser to modify web pages.
ScriptCat's API is based on the Tampermonkey/Greasemonkey `GM_*` API surface.
We are targeting modern chrome-based browsers.

## ScriptCat docs

- API reference: https://docs.scriptcat.org/en/docs/dev/api/
- Metadata block: https://docs.scriptcat.org/en/docs/dev/meta/
- CatApi (ScriptCat-specific extensions): https://docs.scriptcat.org/en/docs/dev/cat-api/
- Example scripts: https://github.com/scriptscat/scriptcat/tree/main/example

## ScriptCat compatibility notes (learned during migration)

- **`@connect` is required** for any host reached via `GM_xmlhttpRequest` or `GM_download` (native mode). Without it, ScriptCat prompts the user for authorization on every request. Declare one `@connect <host>` per remote host.
- **`@grant addStyle` is invalid.** The correct grant is `GM_addStyle`. A bare `addStyle` is silently ignored and the API won't be available.
- **`@grant none` + another `@grant` is contradictory.** `none` means "run in the page with no GM APIs"; pick one or the other.
- **`@updateURL` requires `@downloadURL`** to function. If only `@downloadURL` is set, update checks may not fire. Set both to the same GitHub raw URL.
- **GitHub raw URLs** for `@downloadURL`/`@updateURL` must use `raw.githubusercontent.com` and match the actual file path in the repo (including correct case and `.user.js` extension).
- **`.user.js` extension is required** for ScriptCat to recognize a file as a userscript on install. Files named `.js` won't auto-install.
- **`unsafeWindow` must be declared** via `@grant unsafeWindow` to access page globals (`g_ck`, `g_form`, etc.). ScriptCat injects into the page environment by default (`@inject-into page`), so `unsafeWindow === window` in that mode — but declaring it keeps scripts portable to sandboxed managers.
- **`@run-at` should be explicit.** Default timing can vary; use `document-idle` for scripts that need page globals/DOM, `document-end` for DOM-ready, `document-start` for early injection.
- **`fetch()` to cross-origin hosts hits CORS.** Use `GM_xmlhttpRequest` (with `@connect`) instead — it bypasses CSP and CORS.
- **`@include *` is overly broad** when `@match` already scopes the script. Prefer `@match` alone; only use `@include` for non-standard URL globbing that `@match` patterns can't express.
- **IIFEs must be invoked.** A `(function () { ... })` without trailing `()` defines but never runs the function — use `(function () { ... })()`.
- **ScriptCat does not support `@inject-into auto`** (Tampermonkey's automatic CSP-based content/page switching). Default is `page`; use `@inject-into content` explicitly if CSP is a problem.