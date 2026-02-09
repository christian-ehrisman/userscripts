//set current.time_worked to one second.
// ==UserScript==
// @name     ServiceNow Fixes
// @description Functionally equivalent to clicking the "Start" button on the time worked button right before hitting save/submit in ServiceNow. Does not interfere with other use of the time tracking fields
// @version 1.61
// @match  https://*.service-now.com/*
// @grant    GM_addStyle
// @downloadURL https://github.com/christian-ehrisman/userscripts/raw/refs/heads/master/ServiceNow/ServiceNow_fixes.user.js
// @author  Christian Ehrisman
// ==/UserScript==

// Get current time_worked value
var currentTimeWorked = g_form.getValue('time_worked');

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
g_form.setValue('time_worked', newTimeWorked);


// fix form selection background color
var styleEl = document.createElement("style");
styleEl.textContent = "body::selection { background-color: revert !important; }";
document.body.appendChild(styleEl);
