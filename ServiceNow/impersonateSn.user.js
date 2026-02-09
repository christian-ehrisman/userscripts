// ==UserScript==
// @name            Impersonate SN User
// @description     administrator impersonation script
// @version         0.93
// @author          Christian Ehrisman
// @downloadURL     https://raw.githubusercontent.com/christian-ehrisman/userscripts/refs/heads/master/ServiceNow/impersonateSn.user.js
// @match           https://*.service-now.com/*
// @include         *
// @grant           GM_registerMenuCommand
// @grant           GM_xmlhttpRequest
// @grant           unsafeWindow
// ==/UserScript==

(function () {

    'use strict';
    const cje = "97ca5b0804471580648e3ee6788cc05e";
    const admin = "cc4f96a8dbe3c0901e16034b8a9619b3";
    function updateName(nameTarget) {
        let currentName = document.getElementsByClassName("user-name hidden-xs hidden-sm hidden-md")[0]
        if (currentName.innerHTML !== nameTarget) {
            currentName.innerHTML = nameTarget
            currentName.style.color = "#FFCCCB"
        }

    }
    function impersonateCje() {
        let name = "Christian Ehrisman(cje6)"
        GM_xmlhttpRequest({
            method: "POST",
            url: "https://duke.service-now.com/api/now/ui/impersonate/" + cje,
            headers: {
                "X-UserToken": g_ck,
            }
        })
        updateName(name)
        console.log('l done')
    };
    function impersonateAdmin() {
        let name = "Christian Ehrisman(cje6.sa)"


        GM_xmlhttpRequest({
            method: "POST",
            url: "https://duke.service-now.com/api/now/ui/impersonate/" + admin,
            headers: {
                "X-UserToken": g_ck,
            }
        })
        updateName(name)
        console.log('x done')
    };


    GM_registerMenuCommand('cje6', impersonateCje);
    GM_registerMenuCommand('admin', impersonateAdmin);


})();

