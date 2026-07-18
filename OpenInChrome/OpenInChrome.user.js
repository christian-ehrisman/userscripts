// ==UserScript==
// @name         Open In Chrome (route matched URLs to another Chrome)
// @namespace    https://github.com/christian-ehrisman/userscripts
// @version      1.0.0
// @description  Intercepts clicks on matched links and re-opens them in a different (relabeled) Chrome via a BetterTouchTool named trigger. Runs in personal Chrome; sends work URLs to Duke Chrome.
// @author       Christian Ehrisman
// @homepageURL  https://github.com/christian-ehrisman/userscripts/tree/master/OpenInChrome
// @match        *://*/*
// @noframes
// @run-at       document-start
// @grant        none
// @downloadURL  https://raw.githubusercontent.com/christian-ehrisman/userscripts/master/OpenInChrome/OpenInChrome.user.js
// @updateURL    https://raw.githubusercontent.com/christian-ehrisman/userscripts/master/OpenInChrome/OpenInChrome.user.js
// ==/UserScript==

/*
 * ── BetterTouchTool setup (one-time) ─────────────────────────────────────────
 * Create a BTT named trigger so the userscript has something to call.
 *
 *   1. BTT → "Named & Other Triggers" → "+" → name it exactly: OpenInBrowser
 *   2. Add action: "Run Real JavaScript" and paste:
 *
 *        (async () => {
 *          const url = await get_string_variable({ variable_name: 'targetURL' });
 *          const app = await get_string_variable({ variable_name: 'targetApp' });
 *          if (!url || !app) return;
 *          await runShellScript({
 *            launchPath: '/usr/bin/open',
 *            parameters: `-na;;${app};;${url}`,   // ;;-separated argv, no quoting
 *          });
 *        })();
 *
 *   The btt:// scheme passes targetURL and targetApp through as BTT variables
 *   before the trigger runs. `open -na "<App>" <url>` hands the URL to the
 *   running instance as a new tab (launches it first if it isn't open).
 *
 *   First fire per site: Chrome shows an "Open BetterTouchTool?" prompt —
 *   tick "Always allow" once and it's silent thereafter. If you've enabled
 *   BTT's URL-scheme shared secret, append &shared_secret=... in fire() below.
 * ─────────────────────────────────────────────────────────────────────────────
 */

(() => {
    'use strict';

    const CONFIG = {
        // Must match the BTT named trigger above.
        triggerName: 'OpenInBrowser',

        // First matching rule wins. `hosts` are tested against the link hostname.
        // NOTE: only list hosts that do NOT belong in the browser this is installed
        // in — otherwise a link routes to the same Chrome it's already in.
        rules: [
            {
                app: 'Duke Chrome',
                hosts: [
                    /(^|\.)service-now\.com$/i,
                    /(^|\.)duke\.edu$/i,
                ],
            },
            // Add more destinations as needed, e.g.:
            // { app: 'Personal Chrome', hosts: [/(^|\.)youtube\.com$/i] },
        ],
    };

    const appForUrl = (href) => {
        let host;
        try { host = new URL(href, location.href).hostname; }
        catch { return null; }
        for (const rule of CONFIG.rules) {
            if (rule.hosts.some((re) => re.test(host))) return rule.app;
        }
        return null;
    };

    const fire = (targetUrl, targetApp) => {
        const scheme =
            `btt://trigger_named/?trigger_name=${encodeURIComponent(CONFIG.triggerName)}` +
            `&targetApp=${encodeURIComponent(targetApp)}` +
            `&targetURL=${encodeURIComponent(targetUrl)}`;
        // hidden iframe fires the custom scheme without navigating the current tab
        const frame = document.createElement('iframe');
        frame.style.display = 'none';
        frame.src = scheme;
        (document.body || document.documentElement).appendChild(frame);
        setTimeout(() => frame.remove(), 500);
    };

    const onClick = (e) => {
        // primary click (0) arrives via 'click'; middle click (1) via 'auxclick'
        if (e.button !== 0 && e.button !== 1) return;
        const anchor = e.target?.closest?.('a[href]');
        if (!anchor) return;
        const href = anchor.href;
        if (!/^https?:/i.test(href)) return;
        const app = appForUrl(href);
        if (!app) return;
        e.preventDefault();
        e.stopImmediatePropagation();
        fire(href, app);
    };

    // capture phase so we win before the page's own handlers / SPA routers
    document.addEventListener('click', onClick, true);
    document.addEventListener('auxclick', onClick, true);
})();