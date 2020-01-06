"""
The open challenge solution consists of these actions

request (asynchronous)
* User sends a challenge match by calling `svc.create`
    * Add the request to the cache with a max_age (e.g. 180) second timeout
    * Add the request to ndb, timestamped
    * If the user makes other requests to create a challenge, they
      are denied if there is an entry in the cache. If there is no
      entry in memcache, we check the db, if the entry still
      exists there, we add a new entry to memcache and keep the request in
      the db.

withdraw (asynchronous)
* User withdraws a match by calling `svc.withdraw`
    * Remove the entry from the cache
    * Remove the entry from the db

match (synchronous)
* Every match_rate (e.g. 5) seconds, a task runner fetches all requests that are within
  a max_age (e.g. 180) second time frame
  * The matcher groups all challenges with the same conditions, taking elo
    rating into account.
  * If the matcher finds a match, it starts a game between the two players
    and deletes entries in the db and the cache.
    Some requests will not match during this match cycle, and they are simply
    ignored.

Caveats:

* A user might have left the site with an open request. If it's matched
  they might miss that a new game has been started. This is probably only
  an issue if the user is starting a timed game. This can be resolved by 
  ensuring that timed games are cancelled without change to stats (ELO
  in particular) if neither player makes a move within a timeframe.
* It's possible that the user can create a new request right after
  a match has been made for them, they might then start two games, which
  again is mostly an issue in timed games. This can also be resolved by
  allowing games to silently cancel, but we could also resolve it by allowing
  only one timed auto-challenge game per user. 
* A similar condition arises if the user withdraws the challenge just as the
  matcher is creating a new game. This might irritate some players, but
  one (e.g.) chess.com this is how the matching works. As with other
  sync/async issues we can run into, allowing games to silently cancel
  makes this less of a problem.
"""

import uuid
from google.appengine.api import memcache


class ChallengeService(object):
    def __init__(self, max_age=180, match_rate=5):
        self.cache = ChallengeCacheMemcache(max_age)
        self.max_age = max_age
        self.match_rate = match_rate

    def request(self, user_id, prefs):
        """
        Creates an open challenge for this user.
        """

        self.cache.set(user_id)

    def active_request(self, user_id):
        """
        Returns True if the user has an active request
        """
        if self.cache.has(user_id):
            return True


    def withdraw(self, user_id):
        """
        Removes any open challenge this user may have
        """

    def match(self):
        """
        Reads recent challenges that have been created and creates all acceptable
        matches.
        
        There should be only a single reader per application so no-one
        will be matched more than once per request.
        """


class ChallengeCacheMemcache(object):
    def __init__(self, expires_in_sec):
        self.namespace = "challenge:1"
        self.expires_in_sec = expires_in_sec

    def set(self, user_id):
        memcache.set(user_id, self, time=self.expires_in_sec, namespace=self.namespace)

    def get(self, user_id):
        return memcache.get(user_id, namespace=self.namespace)

    def has(self, user_id):
        return self.get(user_id) != None


class ChallengeExists(Exception):
    pass
