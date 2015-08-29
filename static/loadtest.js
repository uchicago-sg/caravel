/*
 * This script ensures that the new site is able to sustain the same level of
 * load as the old one. It is invoked via script inclusion.
 */
window.addEventListener('load', function() {
    var categories = [
        'apartments', 'subleases', 'appliances', 'bikes', 'books', 'cars',
        'electronics', 'employment', 'furniture', 'miscellaneous', 'services',
        'wanted', 'free'
    ];

    var path = window.location.pathname.substring(1);
    if (categories.indexOf(path) >= 0)
        path = '?q=' + path;

    if (path.startsWith("users"))
        return;

    var iframe = document.createElement('iframe');
    iframe.src = 'https://hosted-caravel.appspot.com/' + path;
    iframe.style.display = 'none';

    var body = document.getElementsByTagName('body')[0];
    body.appendChild(iframe); 
});