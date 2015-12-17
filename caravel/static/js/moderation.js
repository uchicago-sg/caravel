/**
 * Moderation widget.
 *
 * Enables simple, stupid AJAX buttons.
 */

var enableModeration = function(csrfToken) {
    var buttons = document.querySelectorAll("[data-approve]");
    
    [].forEach.call(buttons, function(elem) {
        elem.addEventListener("click", function() {
            var this_ = this, xhr = new XMLHttpRequest;
            xhr.open("POST", "/moderation", true);
            this_.parentNode.parentNode.style.opacity = 0.5;
            xhr.onreadystatechange = function() {
                if (xhr.status >= 200 && xhr.status < 300) {
                    this_.parentNode.parentNode.remove();
                } else {
                    console.error("XHR FAILED");
                }
            };
            xhr.setRequestHeader("Content-type",
                    "application/x-www-form-urlencoded");
            xhr.send("csrf_token=" + encodeURIComponent(csrfToken)
                     + "&approve=" + this_.getAttribute("data-approve"));
        });
    });
}