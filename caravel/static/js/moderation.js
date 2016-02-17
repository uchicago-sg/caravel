/**
 * Moderation widget.
 *
 * Enables simple, stupid AJAX buttons.
 */

var enableModeration = function(csrfToken) {
    var buttons = document.querySelectorAll("[data-approve],[data-deny]");
    
    [].forEach.call(buttons, function(elem) {
        elem.addEventListener("click", function() {
            var this_ = this, xhr = new XMLHttpRequest;
            xhr.open("POST", "/moderation", true);
            this_.parentNode.parentNode.remove();
            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4) {
                    if (xhr.status <= 200 || xhr.status > 300)
                        window.alert("XHR FAILED");
                }
            };
            xhr.setRequestHeader("Content-type",
                    "application/x-www-form-urlencoded");
            xhr.send("csrf_token=" + encodeURIComponent(csrfToken)
                     + "&approve=" + (this_.getAttribute("data-approve") || "")
                     + "&deny=" + (this_.getAttribute("data-deny") || ""));
        });
    });
}
