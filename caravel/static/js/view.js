$(document).ready(function() {
    $("div#thumbnail-toggle").click(function() {
        var data = {v : "thumbnail", q : "{{query}}"};
        $.get('{{url_for("search_listings")}}', data);
    });
    $("div#list-toggle").click(function() {
        var data={v: "list", q:"{{query}}"};
        $.get('/', data);
    })
});
