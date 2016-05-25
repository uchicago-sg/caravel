(function() {
  var nextElement = function(x) {
    x = x.nextSibling;
    while (x && !x.style)
      x = x.nextSibling;
    return x;
  };

  window.addEventListener("DOMContentLoaded", function() {
    var affiliates = document.querySelectorAll("[data-affiliation]");
    [].map.call(affiliates, function(affiliate) {
      /* Extract nodes. */
      var email = nextElement(affiliate.parentNode);
      var button = email.querySelector("a[class^=signin]");
      var field = email.querySelector("input");

      if (!button)
        return;

      /* Remove explainatory text. */
      [].map.call(email.querySelectorAll(".accessibility"), function(elem) {
        elem.remove();
      });

      /* Update which field is visible based on whether the user can sign in. */
      var update = function() {
        var underOsha = (affiliate.value.indexOf("osha") == 0);
        var anySelection = !!affiliate.value;

        button.href = "/oshalogin?affiliation=" +
          encodeURIComponent(affiliate.value);

        email.style.display = anySelection ? 'block' : 'none';
        button.style.display = underOsha ? 'inline-block' : 'none';
        field.style.display = underOsha ? 'none' : 'inline-block';
      };

      affiliate.onchange = update;
      update();
    });
  });
})();