/**
 * The coalesce function ensures that only one invocation of the given function
 * is in flight. When invoked, the first parameter of +action+ is called with
 * a function that allows future invocations to succeed.
 *
 * @param {Function} action What function to wrap.
 * @returns {Function} A transformed function
 */
var coalesce = function(action) {
    var active = false;

    return function() {
        if (active)
            return;

        action.apply(null, [function() {
            active = false;
        }].concat(arguments));
        active = true;
    };
}

/**
 * Loads more listings from the server.
 */
var fetchMore = coalesce(function(complete) {

    var parameterString = window.location.search.substring(1);
    var continuation = "&continuation&offset=" + document.querySelectorAll(".listing").length;

    // Make a background AJAH request.
    var xhr = new XMLHttpRequest;
    xhr.open("GET", "?" + parameterString + continuation, true);
    xhr.onreadystatechange = function() {

        // Ignore events for incomplete requests.
        if (xhr.readyState != 4)
            return;

        // Stop fetching more events if we have nothing to fetch.
        if (xhr.responseText.trim() == "")
            return;

        // Append the results to the existing results <div>
        var frag;
        if (parameterString.indexOf("v=ls") >= 0) {
            frag = document.createElement("table");
            frag.setAttribute("class", "table listing-table table-margin");
        }
        else {
            frag = document.createElement("div");
        }
        frag.innerHTML = xhr.responseText;

        var listings = document.querySelector("#listings");
        listings.appendChild(frag);

        // Prevent too many requests from overloading the server.
        setTimeout(complete, 100);
    }
    xhr.send();

});

/*
 * Load more listings if we're near the end.
 */
window.addEventListener("scroll", function() {
    var total = document.documentElement.scrollHeight;
    var above = window.scrollY;
    var viewport = window.innerHeight;
    var below = total - above - viewport;

    if (below < 5000)
        fetchMore();
});
