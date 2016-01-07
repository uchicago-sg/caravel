from google.appengine.ext import ndb
from caravel.storage import dos


class RateLimitMixin(ndb.Model):

    """
    A RateLimitMixin ensures that the given model will only be created a fixed
    number of times per minute. If the rate limit is violated, the entity is
    treated as though the principal creating it is unviolated.

    >>> from caravel.model.moderation import ModeratedMixin
    >>> from caravel.model.principal import PrincipalMixin
    >>> from caravel.utils import Principal, Device

    >>> class G(RateLimitMixin, ModeratedMixin, PrincipalMixin):
    ...   MAX_BURST_LIMIT = 2

    >>> device = Device('', '', '')
    >>> person_a = Principal('rlt-foo@uchicago.edu', device, 'GOOGLE_APPS')
    >>> person_b = Principal('rlt-bar@uchicago.edu', device, 'GOOGLE_APPS')

    >>> a = G(principal=person_a); a.put() and a.approved()
    True
    >>> a = G(principal=person_a); a.put() and a.approved()
    True
    >>> a = G(principal=person_a); a.put() and a.approved()
    False

    >>> b = G(principal=person_b); b.put() and b.approved()
    True
    """

    MAX_BURST_LIMIT = 0
    MAX_DAILY_LIMIT = 0

    burst_count = ndb.IntegerProperty()
    daily_count = ndb.IntegerProperty()

    def _pre_put_hook(self):
        """
        Compute the current rate and store it in the burst/daily limits.
        """

        if not self.burst_count:
            self.burst_count = dos.current_rate(self.principal.email,
                                                self.MAX_BURST_LIMIT, 60)

        if not self.daily_count:
            self.daily_count = dos.current_rate(self.principal.email,
                                                self.MAX_DAILY_LIMIT,
                                                3600 * 24)

        return super(RateLimitMixin, self)._pre_put_hook()

    def approved(self):
        """
        Ensure that listings must be manually approved.
        """

        if super(RateLimitMixin, self).approved():
            # Allow manual approval.
            if self.principal.validated_by:
                return True

            if self.MAX_BURST_LIMIT and self.burst_count > self.MAX_BURST_LIMIT:
                return False

            if self.MAX_DAILY_LIMIT and self.burst_count > self.MAX_DAILY_LIMIT:
                return False

            return True

        return False
