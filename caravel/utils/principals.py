import uuid

class Device(object):
    @classmethod
    def from_request(klass, request):
        return Device(
            nonce=str(uuid.uuid4()),
            user_agent=request.headers.get("User-agent", ""),
            ip_address=request.remote_addr,
        )

    def __init__(self, nonce, user_agent, ip_address):
        self.nonce, self.user_agent, self.ip_address = (
            nonce, user_agent, ip_address)

    def __repr__(self):
        return "Device(nonce={!r}, user_agent={!r}, ip_address={!r})".format(
            self.nonce, self.user_agent, self.ip_address)

class Principal(object):
    GOOGLE_APPS = "GOOGLE_APPS"
    EMAIL = "EMAIL"
    LEGACY = "LEGACY"

    def __init__(self, email, device, auth_method):
        if auth_method not in (self.GOOGLE_APPS, self.EMAIL, self.LEGACY):
            raise ValueError

        if not isinstance(email, basestring):
            raise TypeError, email

        if not isinstance(device, Device):
            raise TypeError, device

        self.email, self.device, self.auth_method = email, device, auth_method
        self.validated_by = ""

    @property
    def valid(self):
        """
        Returns why this principal is valid.
        """

        return ((self.auth_method in (self.GOOGLE_APPS, self.LEGACY))
                 or bool(self.validated_by))

    def validate(self, reason):
        """
        Sets the reason why this Principal was validated.
        """

        self.validated_by = reason

    def __repr__(self):
        """
        Returns a readable representation of this Principal.
        """

        return "Principal(email={!r}, device={!r}, auth_method={!r})".format(
            self.email, self.device, self.auth_method)