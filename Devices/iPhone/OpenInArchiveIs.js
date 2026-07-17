// ==UserScript==
// @name         Archive.is - Open Newest
// @description  Open the newest archive.is snapshot of the current page
// @match        *://*/*
// @version      1.0
// @run-at       document-end
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    
    // Create floating button
    const button = document.createElement('button');
    button.innerHTML = '📦';
    button.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 25px;
        background: #333;
        color: white;
        border: none;
        font-size: 24px;
        cursor: pointer;
        z-index: 999999;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    `;
    
    button.addEventListener('click', openNewestArchive);
    document.body.appendChild(button);
    
    function openNewestArchive() {
        const currentUrl = window.location.protocol + "//" + window.location.hostname + window.location.pathname;
        const archiveSearchUrl = "https://archive.is/" + encodeURI(currentUrl);
        
        // Show loading state
        button.innerHTML = '⏳';
        
        fetch(archiveSearchUrl)
            .then(r => r.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newestLink = doc.querySelector('.TEXT-BLOCK a[href^="/"]');
                
                if (newestLink) {
                    window.location.href = "https://archive.is" + newestLink.getAttribute('href');
                } else {
                    window.location.href = archiveSearchUrl;
                }
            })
            .catch(() => {
                window.location.href = archiveSearchUrl;
            })
            .finally(() => {
                button.innerHTML = '📦';
            });
    }
})();


