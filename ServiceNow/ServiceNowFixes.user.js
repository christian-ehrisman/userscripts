// ==UserScript==
// @name        ServiceNow Fixes
// @namespace   https://github.com/christian-ehrisman/userscripts
// @description Functionally equivalent to clicking the "Start" button on the time worked button right before hitting save/submit in ServiceNow. Does not interfere with other use of the time tracking fields
// @version     1.61
// @match       https://*.service-now.com/*
// @run-at      document-idle
// @grant       GM_addStyle
// @grant       unsafeWindow
// @downloadURL https://raw.githubusercontent.com/christian-ehrisman/userscripts/refs/heads/master/ServiceNow/ServiceNowFixes.user.js
// @updateURL   https://raw.githubusercontent.com/christian-ehrisman/userscripts/refs/heads/master/ServiceNow/ServiceNowFixes.user.js
// @author      Christian Ehrisman
// ==/UserScript==

(function () {
    'use strict';

    // Access the ServiceNow form API via the page's global scope.
    // In ScriptCAT's default page-injection mode unsafeWindow === window,
    // but referencing it explicitly keeps the script portable across
    // sandboxed managers (Violentmonkey, Tampermonkey).
    var gForm = unsafeWindow.g_form;
    if (typeof gForm === 'undefined') {
        console.warn('[ServiceNow Fixes] g_form is not available on this page.');
        return;
    }

    // Get current time_worked value
    var currentTimeWorked = gForm.getValue('time_worked');

    // Parse the current time (format: HH:MM:SS or empty)
    var totalSeconds = 0;
    if (currentTimeWorked && currentTimeWorked !== '') {
        var parts = currentTimeWorked.split(':');
        totalSeconds = (parseInt(parts[0]) * 3600) + (parseInt(parts[1]) * 60) + parseInt(parts[2]);
    }

    // Add 1 second
    totalSeconds += 1;

    // Convert back to HH:MM:SS format
    var hours = Math.floor(totalSeconds / 3600);
    var minutes = Math.floor((totalSeconds % 3600) / 60);
    var seconds = totalSeconds % 60;

    var newTimeWorked =
        String(hours).padStart(2, '0') + ':' +
        String(minutes).padStart(2, '0') + ':' +
        String(seconds).padStart(2, '0');

    // Set the new value
    gForm.setValue('time_worked', newTimeWorked);

    // Fix form selection background color (GM_addStyle bypasses CSP)
    GM_addStyle("body::selection { background-color: revert !important; }");
})();
