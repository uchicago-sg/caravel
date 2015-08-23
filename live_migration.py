import state

from google.appengine.api import mail

def pull_from_listing(permalink):
    """
    Retrieves the listing from the old Marketplace, and save it to the database.
    If the pull fails, the code automatically emails an administrator to report
    it.
    """

    try:
        # Retrieve existing listing by the permalink.
        if not re.match(r"^[a-zA-Z\-0-9]+$", permalink):
            raise ValueError("Invalid permalink: {!r}".format(permalink))
        url = "http://marketplace.uchicago.edu/{}.json".format(permalink)
        json_data = json.load(urllib2.urlopen(url))

        # Parse the listing date from not-quite-ISO8601 to App Engine UTC.
        posted_at = datetime.datetime.strptime(
            json_data["renewed_at"][:-6], "%Y-%m-%dT%H:%M:%S"
        ) - datetime.timedelta(
            hours=float(json_data["renewed_at"][-6:-3]),
            minutes=float(json_data["renewed_at"][-2:])
        )

        # (Idempotently) save this entity into the datastore.
        state.Listing(
            id=json_data["permalink"],
            seller=json_data["seller"]["email"],
            posted_at=posted_at.replace(tzinfo=None),
            description=json_data["description"],
            details=json_data["details"],
            price=(int(float(json_data["price"]) * 100))
        ).put()

    except Exception:
        mail.send_mail(
            "noreply@hosted-caravel.appspotmail.com",
            "open-source@fatlotus.com",
            "Automatic Parsing Failed",
            permalink
        )
        raise
