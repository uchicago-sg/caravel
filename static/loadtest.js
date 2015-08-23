/*
 * This script ensures that the new site is able to sustain the same level of
 * load as the old one. It is invoked via script inclusion.
 */
window.addEventListener('load', function() {
    var iframe = document.createElement('iframe');
    iframe.src = 'https://hosted-caravel.appspot.com' +
         window.location.pathname;
    iframe.style.display = 'none';

    var body = document.getElementsByTagName('body')[0];
    body.appendChild(iframe); 
});