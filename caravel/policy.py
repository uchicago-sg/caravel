def is_authorized_seller(email):
    """Returns true if the user can use Marketplace to sell things."""
    try:
        user, domain = email.split("@")
        return domain in ["uchicago.edu", "uchospitals.edu", "chicagobooth.edu"]
    except ValueError:
        return False

def is_authorized_buyer(email):
    """Returns true if the user can use Marketplace to sell things."""
    try:
        user, domain = email.split("@")
        return bool(domain)
    except ValueError:
        return False