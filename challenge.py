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
  - Finally, it removes the matchedkitems from the datastore and commits the transaction.
"""
import logging


class ChallengeService:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def add_challenge(self, challenge):
        """
        Adding a new challenge object adds the challenge to:
            * The user's session (for showing it in the UI and cancelling)
            * Memcache
        :return:
        """
        self.logger.debug("Creating a challenge: {}".format(challenge))


