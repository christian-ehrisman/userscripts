// ==UserScript==
// @name        Kill Sticky
// @namespace   Violentmonkey Scripts
// @match       https://medium.com/
// @grant       none
// @version     1.0
// @author      -
// @description 2/13/2023, 2:58:47 PM
// @grant addStyle
// ==/UserScript==
(function () {
    document.querySelectorAll("body *").forEach(function (node) {
        if (["fixed", "sticky"].includes(getComputedStyle(node).position)) {
            node.parentNode.removeChild(node);
        }
    });
    document.querySelectorAll("html *").forEach(function (node) {
        var s = getComputedStyle(node);
        if ("hidden" === s["overflow"]) {
            node.style["overflow"] = "visible";
        }
        if ("hidden" === s["overflow-x"]) {
            node.style["overflow-x"] = "visible";
        }
        if ("hidden" === s["overflow-y"]) {
            node.style["overflow-y"] = "visible";
        }
    });
    var htmlNode = document.querySelector("html");
    htmlNode.style["overflow"] = "visible";
    htmlNode.style["overflow-x"] = "visible";
    htmlNode.style["overflow-y"] = "visible";
})
