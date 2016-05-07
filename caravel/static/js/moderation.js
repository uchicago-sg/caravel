/**
 * Moderation widget.
 *
 * Enables simple, stupid AJAX buttons.
 */

var enableModeration = function(csrfToken) {
    var buttons = document.querySelectorAll(
      "[data-skip],[data-approve],[data-deny]");
    
    var siblingWithChildren = function(x) {
      do {
        x = x.nextSibling;
      } while (!x.childNodes);
      return x;
    };

    [].forEach.call(buttons, function(elem) {
        elem.addEventListener("click", function() {
            var automod = document.getElementById("automod");
            console.log(elem.outerHTML);
            var container = elem.parentNode.parentNode.parentNode.parentNode;
            var next = siblingWithChildren(container).childNodes[5];
            var anyMoreToModerate = !!next;
            if (anyMoreToModerate)
              next.appendChild(automod);
            container.remove();

            elem.parentNode.parentNode.parentNode.parentNode.remove();

            if (elem.getAttribute("data-skip")) {
              if (!anyMoreToModerate)
                window.location.reload();
            }

            /* persist the change in moderation */
            var xhr = new XMLHttpRequest;
            xhr.open("POST", "/moderation", true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4) {
                    if (xhr.status < 200 || xhr.status >= 300)
                        window.alert("XHR FAILED: " + xhr.status);
                    else if (!anyMoreToModerate)
                        window.location.reload();
                }
            };
            xhr.setRequestHeader("Content-type",
                    "application/x-www-form-urlencoded");
            xhr.send("csrf_token=" + encodeURIComponent(csrfToken)
                     + "&approve=" + (elem.getAttribute("data-approve") || "")
                     + "&deny=" + (elem.getAttribute("data-deny") || ""));
        });
    });
}
