"""
challenge.py

Allows users to create open challenges which are automatically
matched based on ELO rating.

Design
------
* User sends in a `ChallengeModel` object via the REST interface,
  which gets forwarded to add_challenge
* The challenge object is saved in the datastore. There is an index for the challenge
  object's properties, so `fetch all challenges with bag_version=?, duration=?, no_cheat=?`.
  will be fast.
* Furthermore, to minimize reads, the count for the challenge type is updated in memcache:
  If the user adds (bag_version=1,duration=15) we read the cache key "challenges",
  using Compare-And-Set (ensures no race conditions). This object is a regular
  Python dictionary object, which contains key/value pairs of the form
  `unique_challenge_type_key`=>`count`, e.g. 1_15_0=>3
* A background task runs regularly, e.g. every 5 seconds.
  - It first checks memcache to see which keys contain enough players (more than one).
  - It looks up the challenges within a transaction, (so users can not cancel challenges
    until this operation is over for consistency).
  - It then matches as many games as possible from this set, minimizing ELO rating difference
  - Finally, it updates the counter object again, decreasing each key by the number
    of matched games for each (note that it might have been updated in the meantime, so
    the task must decrease the current values)
  - Finally, it removes the matcheditems from the datastore and commits the transaction.
"""
import logging
from google.appengine.ext import ndb
from google.appengine.api import memcache
from skrafldb import OpenChallengeModel, UserModel
from google.appengine.ext import ndb


class ChallengeService:
    CACHE_KEY = "OpenChallengeCounts"

    # TODO: Rename to OpenChallengeService
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def status(self, cache=True, datastore=False):
        """Fetches the status of the challenges"""
        ret = dict()
        if cache:
            client = memcache.Client()
            ret["cached"] = client.gets(self.CACHE_KEY)

        if datastore:
            OpenChallengeModel.count_all_types()


        return ret

    def count_challenges(self):
        """Counts all open challenges in the datastore"""
        return dict()

    def refresh_memcache_count(self):
        """
        Refreshes the memcache count based on all known challenge types.
        Called if the count is not available in memcache (or needs to be refreshed
        for another reason)
        :return:
        """

        # TODO: Count all challenges of all types (group by)
        client = memcache.Client()
        fresh = self.count_challenges()
        client.set(self.CACHE_KEY, fresh)
        return fresh

    def get_cache_counts(self):
        """
        Returns the challenge type counts from the counts,
        refreshing them if they don't already exist
        :return:
        """
        client = memcache.Client()
        counter_dict = client.gets(self.CACHE_KEY)
        if counter_dict is None:
            counter_dict = self.refresh_memcache_count()
        return counter_dict

    def match_all(self):
        """
        Matches all outstanding challenges.

        The matching algorithm is rather naive. It doesn't minimize the difference in
        ELO ratings (for simplicity, since such an algorithm would also have to ensure
        that outliers would still be matched), but instead it:
          * orders challenges in rating order, either asc. or desc. (randomly chosen, so that it's as likely that
            it's as likely that the lowest rated challenge get's matched as the highest rated one, since in the
            case when the number of challenges is odd, the last item will not get matched)
          * visits the first pair in the list, matches it, then goes on to the next pair after that until
            there is zero or one item left.
        :return:
        """
        # TODO: This should come from a cache to make it as cheap as possible
        # Also: ensure that when removing from the model, the automated cache gets updated
        from skrafldb import OpenChallengeTypeModel
        challenge_types = OpenChallengeTypeModel.get_all_having_at_least(2)
        for challenge_type in challenge_types:
            challenges = OpenChallengeModel.get_by_challenge_type(challenge_type.key)
            print challenge_type.key, challenges
            for challenge in challenges:
                print challenge

    def add_challenge(self, user, duration, bag_version, no_cheat):
        """
        Adding a new challenge object adds the challenge to:
          - NDB (OpenChallengeModel)
          - memcache: Maintains counts to limit access to the backend
            (since the open challenges status will be queried a lot, e.g. every 5 secs)

        The method uses an ndb transaction to ensure that if another
        process changes the same ndb key, at the same time, it will fail.
        This is to ensure that if the user cancels the request in another request
        (or some other change is made) the counter in memcache will be consistent.

        :return:
        """
        # TODO: The platform retries the action 3 times on collision failures
        # If it fails in all three, a TransactionFailedError is thrown.
        # Decide if we want to throw another exception instead
        self.logger.debug("Creating a challenge: {}".format(duration))
        user_key = ndb.Key(UserModel, user.id())

        if not OpenChallengeModel.exists(user_key, user.human_elo(), duration,
                                         bag_version, no_cheat):
            OpenChallengeModel.add(user_key,
                                   user.human_elo(), duration, bag_version, no_cheat)
        else:
            raise OpenChallengeAlreadyExists()


class OpenChallengeAlreadyExists(Exception):
    pass
