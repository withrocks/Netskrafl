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
* To minimize reads, the count for the challenge type is updated in memcache:
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

    @ndb.transactional
    def add_challenge(self, user, duration, bag_version, no_cheat):
        """
        Adding a new challenge object adds the challenge to:
          - NDB (OpenChallengeModel)
          - memcache: Maintains counts to limit access to the backend
            (since the open challenges status will be challenged a lot)

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
        user_id = ndb.Key(UserModel, user.id())
        challenge_type = OpenChallengeModel.add(user_id,
                                       user.human_elo(), duration, bag_version, no_cheat)

        if challenge_type:
            # This is a newly added challenge type by this user. Update the counters.

            # Update the memcache key for this, note that we use the compare-and-set
            # operation and we only increase the count so it should be in synch
            # with changes to other challenges.
            client = memcache.Client()
            for x in xrange(0, 10):
                # Retry only a few times. If this fails, we'll simply have
                # one too few items counted. This could be corrected by
                # a separate task which cleans up (calculates the actual state)
                # once every x minutes (TODO)
                print "Trying to set key for {}".format(challenge_type)
                counter_dict = client.gets(self.CACHE_KEY)
                if counter_dict is None:
                    counter_dict = self.refresh_memcache_count()

                # The counter_dict is a Python dictionary, containing all
                # challenge types with known counts:
                if challenge_type not in counter_dict:
                    counter_dict[challenge_type] = 0
                counter_dict[challenge_type] += 1

                if client.cas(self.CACHE_KEY, counter_dict):
                    print "Successfully added the key"
                    break

