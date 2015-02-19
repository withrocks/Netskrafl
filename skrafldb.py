# -*- coding: utf-8 -*-

""" Skrafldb - persistent data management for the Netskrafl application

    Author: Vilhjalmur Thorsteinsson, 2014

    This module stores data in the Google App Engine NDB
    (see https://developers.google.com/appengine/docs/python/ndb/).

    The data model is as follows:

    UserModel:
        nickname : string
        inactive : boolean
        prefs : dict
        timestamp : timestamp

    MoveModel:
        coord : string
        tiles : string # Blanks are denoted by '?' followed by meaning
        score : integer
        rack : string # Contents of rack after move
        timestamp : timestamp

    GameModel:
        player0 : key into UserModel
        player1 : key into UserModel
        irack0 : string # Initial rack
        irack1 : string
        rack0 : string # Current rack
        rack1 : string
        score0 : integer
        score1 : integer
        to_move : integer # Whose move is it, 0 or 1
        over : boolean # Is the game over?
        timestamp : timestamp # Start time of game
        ts_last_move : timestamp # Time of last move
        moves : array of MoveModel

    FavoriteModel:
        parent = key into UserModel
        destuser: key into UserModel

    ChallengeModel:
        parent = key into UserModel
        destuser : key into UserModel
        timestamp : timestamp
        prefs : dict

"""

import logging
import threading
import uuid

from datetime import datetime, timedelta

from google.appengine.ext import ndb
from google.appengine.api import channel

from languages import Alphabet


class Unique:
    """ Wrapper for generation of unique id strings for keys """

    @staticmethod
    def id():
        """ Generates unique id strings """
        return str(uuid.uuid1()) # Random UUID


class UserModel(ndb.Model):

    """ Models an individual user """

    nickname = ndb.StringProperty(indexed = True)
    inactive = ndb.BooleanProperty()
    prefs = ndb.JsonProperty()
    timestamp = ndb.DateTimeProperty(auto_now_add = True)
    # Ready for challenges?
    ready = ndb.BooleanProperty(required = False, default = False)
    # Ready for timed challenges?
    ready_timed = ndb.BooleanProperty(required = False, default = False)

    @classmethod
    def create(cls, user_id, nickname):
        """ Create a new user """
        user = cls(id = user_id)
        user.nickname = nickname # Default to the same nickname
        user.inactive = False # A new user is always active
        user.prefs = { } # No preferences
        user.ready = False # Not ready for new challenges unless explicitly set
        user.ready_timed = False # Not ready for timed games unless explicitly set
        return user.put().id()

    @classmethod
    def update(cls, user_id, nickname, inactive, prefs, ready, ready_timed):
        """ Update an existing user entity """
        user = cls.fetch(user_id)
        user.nickname = nickname
        user.inactive = inactive
        user.prefs = prefs
        user.ready = ready
        user.ready_timed = ready_timed
        user.put()

    @classmethod
    def fetch(cls, user_id):
        """ Fetch a user entity by id """
        return cls.get_by_id(user_id)

    @classmethod
    def count(cls):
        """ Return a count of user entities """
        return cls.query().count()

    @classmethod
    def list(cls, nick_from, nick_to, max_len = 100):
        """ Query for a list of users within a nickname range """

        nick_from = u"a" if nick_from is None else Alphabet.tolower(nick_from)
        nick_to = u"ö" if nick_to is None else Alphabet.tolower(nick_to)
        counter = 0

        try:
            o_from = Alphabet.full_order.index(nick_from[0])
        except:
            o_from = 0
        try:
            o_to = Alphabet.full_order.index(nick_to[0])
        except:
            o_to = len(Alphabet.full_order) - 1

        # We do this by issuing a series of queries, each returning
        # nicknames beginning with a particular letter.
        # These shenanigans are necessary because NDB maintains its string
        # indexes by Unicode ordinal index, which is quite different from
        # the actual sort collation order we need. Additionally, the
        # indexes are case-sensitive while our query boundaries are not.

        # Prepare the list of query letters
        q_letters = []

        for i in range(o_from, o_to + 1):
            # Append the lower case letter
            q_letters.append(Alphabet.full_order[i])
            # Append the upper case letter
            q_letters.append(Alphabet.full_upper[i])

        # For aesthetic cleanliness, sort the query letters (in Unicode order)
        q_letters.sort()

        for q_from in q_letters:

            q_to = unichr(ord(q_from) + 1)

            # logging.info(u"Issuing user query from '{0}' to '{1}'".format(q_from, q_to).encode('latin-1'))
            q = cls.query(ndb.AND(UserModel.nickname >= q_from, UserModel.nickname < q_to))

            CHUNK_SIZE = 1000 # Individual letters contain >600 users as of 2015-02-12
            offset = 0
            go = True
            while go:
                chunk = 0
                # logging.info(u"Fetching chunk of {0} users".format(CHUNK_SIZE).encode('latin-1'))
                for um in q.fetch(CHUNK_SIZE, offset = offset):
                    chunk += 1
                    if not um.inactive:
                        # This entity matches: return a dict describing it
                        yield dict(
                            id = um.key.id(),
                            nickname = um.nickname,
                            prefs = um.prefs,
                            timestamp = um.timestamp,
                            ready = um.ready,
                            ready_timed = um.ready_timed
                        )
                        counter += 1
                        if max_len > 0 and counter >= max_len:
                            # Hit limit on returned users: stop iterating
                            return
                if chunk < CHUNK_SIZE:
                    # Hit end of query: stop iterating
                    go = False
                else:
                    # Continue with the next chunk
                    offset += chunk


class MoveModel(ndb.Model):
    """ Models a single move in a Game """

    coord = ndb.StringProperty()
    tiles = ndb.StringProperty()
    score = ndb.IntegerProperty(default = 0)
    rack = ndb.StringProperty(required = False, default = None)
    timestamp = ndb.DateTimeProperty(required = False, default = None)


class GameModel(ndb.Model):
    """ Models a game between two users """

    # The players
    player0 = ndb.KeyProperty(kind = UserModel)
    player1 = ndb.KeyProperty(kind = UserModel)

    # The racks
    rack0 = ndb.StringProperty(indexed = False)
    rack1 = ndb.StringProperty(indexed = False)

    # The scores
    score0 = ndb.IntegerProperty()
    score1 = ndb.IntegerProperty()

    # Whose turn is it next, 0 or 1?
    to_move = ndb.IntegerProperty()

    # How difficult should the robot player be (if the opponent is a robot)?
    # None or 0 = most difficult
    robot_level = ndb.IntegerProperty(required = False, indexed = False, default = 0)

    # Is this game over?
    over = ndb.BooleanProperty()

    # When was the game started?
    timestamp = ndb.DateTimeProperty(auto_now_add = True)

    # The timestamp of the last move in the game
    ts_last_move = ndb.DateTimeProperty(required = False, default = None)

    # The moves so far
    moves = ndb.LocalStructuredProperty(MoveModel, repeated = True)

    # The initial racks
    irack0 = ndb.StringProperty(required = False, indexed = False, default = None)
    irack1 = ndb.StringProperty(required = False, indexed = False, default = None)

    # Game preferences, such as duration, alternative bags or boards, etc.
    prefs = ndb.JsonProperty(required = False, default = None)

    def set_player(self, ix, user_id):
        """ Set a player key property to point to a given user, or None """
        k = None if user_id is None else ndb.Key(UserModel, user_id)
        if ix == 0:
            self.player0 = k
        elif ix == 1:
            self.player1 = k

    @classmethod
    def fetch(cls, uuid):
        """ Fetch a game entity given its uuid """
        return cls.get_by_id(uuid)

    @classmethod
    def list_finished_games(cls, user_id, max_len = 10):
        """ Query for a list of recently finished games for the given user """
        assert user_id is not None
        if user_id is None:
            return
        k = ndb.Key(UserModel, user_id)
        q = cls.query(ndb.OR(GameModel.player0 == k, GameModel.player1 == k)) \
            .filter(GameModel.over == True) \
            .order(-GameModel.ts_last_move)

        def game_callback(gm):
            """ Map a game entity to a result dictionary with useful info about the game """
            uuid = gm.key.id()
            u0 = None if gm.player0 is None else gm.player0.id()
            u1 = None if gm.player1 is None else gm.player1.id()
            if u0 == user_id:
                # Player 0 is the source player, 1 is the opponent
                opp = u1
                sc0, sc1 = gm.score0, gm.score1
            else:
                # Player 1 is the source player, 0 is the opponent
                assert u1 == user_id
                opp = u0
                sc1, sc0 = gm.score0, gm.score1
            return dict(
                uuid = uuid,
                ts = gm.timestamp,
                ts_last_move = gm.ts_last_move or gm.timestamp,
                opp = opp,
                sc0 = sc0,
                sc1 = sc1,
                robot_level = gm.robot_level)

        for gm in q.fetch(max_len):
            yield game_callback(gm)


    @classmethod
    def list_live_games(cls, user_id, max_len = 10):
        """ Query for a list of active games for the given user """
        assert user_id is not None
        if user_id is None:
            return
        k = ndb.Key(UserModel, user_id)
        q = cls.query(ndb.OR(GameModel.player0 == k, GameModel.player1 == k)) \
            .filter(GameModel.over == False) \
            .order(-GameModel.ts_last_move)

        def game_callback(gm):
            """ Map a game entity to a result tuple with useful info about the game """
            uuid = gm.key.id()
            u0 = None if gm.player0 is None else gm.player0.id()
            u1 = None if gm.player1 is None else gm.player1.id()
            if u0 == user_id:
                # Player 0 is the source player, 1 is the opponent
                opp = u1
                sc0, sc1 = gm.score0, gm.score1
                my_turn = (gm.to_move == 0)
            else:
                # Player 1 is the source player, 0 is the opponent
                assert u1 == user_id
                opp = u0
                sc1, sc0 = gm.score0, gm.score1
                my_turn = (gm.to_move == 1)
            return dict(
                uuid = uuid,
                ts = gm.ts_last_move or gm.timestamp,
                opp = opp,
                my_turn = my_turn,
                sc0 = sc0,
                sc1 = sc1,
                robot_level = gm.robot_level)

        for gm in q.fetch(max_len):
            yield game_callback(gm)


class FavoriteModel(ndb.Model):
    """ Models the fact that a user has marked another user as a favorite """

    MAX_FAVORITES = 100 # The maximum number of favorites that a user can have

    # The originating (source) user is the parent/ancestor of the relation
    destuser = ndb.KeyProperty(kind = UserModel)

    def set_dest(self, user_id):
        """ Set a destination user key property """
        k = None if user_id is None else ndb.Key(UserModel, user_id)
        self.destuser = k

    @classmethod
    def list_favorites(cls, user_id, max_len = MAX_FAVORITES):
        """ Query for a list of favorite users for the given user """
        assert user_id is not None
        if user_id is None:
            return
        k = ndb.Key(UserModel, user_id)
        q = cls.query(ancestor = k)
        for fm in q.fetch(max_len):
            yield None if fm.destuser is None else fm.destuser.id()

    @classmethod
    def has_relation(cls, srcuser_id, destuser_id):
        """ Return True if destuser is a favorite of user """
        if srcuser_id is None or destuser_id is None:
            return False
        ks = ndb.Key(UserModel, srcuser_id)
        kd = ndb.Key(UserModel, destuser_id)
        q = cls.query(ancestor = ks).filter(FavoriteModel.destuser == kd)
        return q.get(keys_only = True) != None

    @classmethod
    def add_relation(cls, src_id, dest_id):
        """ Add a favorite relation between the two users """
        fm = FavoriteModel(parent = ndb.Key(UserModel, src_id))
        fm.set_dest(dest_id)
        fm.put()

    @classmethod
    def del_relation(cls, src_id, dest_id):
        """ Delete a favorite relation between a source user and a destination user """
        ks = ndb.Key(UserModel, src_id)
        kd = ndb.Key(UserModel, dest_id)
        while True:
            # There might conceivably be more than one relation,
            # so repeat the query/delete cycle until we don't find any more
            q = cls.query(ancestor = ks).filter(FavoriteModel.destuser == kd)
            fmk = q.get(keys_only = True)
            if fmk is None:
                return
            fmk.delete()


class ChallengeModel(ndb.Model):
    """ Models a challenge issued by a user to another user """

    # The challenging (source) user is the parent/ancestor of the relation

    # The challenged user
    destuser = ndb.KeyProperty(kind = UserModel)

    # The parameters of the challenge (time, bag type, etc.)
    prefs = ndb.JsonProperty()

    # The time of issuance
    timestamp = ndb.DateTimeProperty(auto_now_add = True)

    def set_dest(self, user_id):
        """ Set a destination user key property """
        k = None if user_id is None else ndb.Key(UserModel, user_id)
        self.destuser = k

    @classmethod
    def has_relation(cls, srcuser_id, destuser_id):
        """ Return True if srcuser has issued a challenge to destuser """
        if srcuser_id is None or destuser_id is None:
            return False
        ks = ndb.Key(UserModel, srcuser_id)
        kd = ndb.Key(UserModel, destuser_id)
        q = cls.query(ancestor = ks).filter(ChallengeModel.destuser == kd)
        return q.get(keys_only = True) != None

    @classmethod
    def find_relation(cls, srcuser_id, destuser_id):
        """ Return (found, prefs) where found is True if srcuser has challenged destuser """
        if srcuser_id is None or destuser_id is None:
            return (False, None)
        ks = ndb.Key(UserModel, srcuser_id)
        kd = ndb.Key(UserModel, destuser_id)
        q = cls.query(ancestor = ks).filter(ChallengeModel.destuser == kd)
        cm = q.get()
        if cm == None:
            # Not found
            return (False, None)
        # Found: return the preferences associated with the challenge (if any)
        return (True, cm.prefs)

    @classmethod
    def add_relation(cls, src_id, dest_id, prefs):
        """ Add a challenge relation between the two users """
        cm = ChallengeModel(parent = ndb.Key(UserModel, src_id))
        cm.set_dest(dest_id)
        cm.prefs = { } if prefs is None else prefs
        cm.put()

    @classmethod
    def del_relation(cls, src_id, dest_id):
        """ Delete a challenge relation between a source user and a destination user """
        ks = ndb.Key(UserModel, src_id)
        kd = ndb.Key(UserModel, dest_id)
        prefs = None
        found = False
        while True:
            # There might conceivably be more than one relation,
            # so repeat the query/delete cycle until we don't find any more
            q = cls.query(ancestor = ks).filter(ChallengeModel.destuser == kd)
            cm = q.get()
            if cm is None:
                # Return the preferences of the challenge, if any
                return (found, prefs)
            # Found the relation in question: store the associated preferences
            found = True
            if prefs is None:
                prefs = cm.prefs
            cm.key.delete()

    @classmethod
    def list_issued(cls, user_id, max_len = 20):
        """ Query for a list of challenges issued by a particular user """
        assert user_id is not None
        if user_id is None:
            return
        k = ndb.Key(UserModel, user_id)
        # List issued challenges in ascending order by timestamp (oldest first)
        q = cls.query(ancestor = k).order(ChallengeModel.timestamp)

        def ch_callback(cm):
            """ Map a favorite relation into a list of users """
            id0 = None if cm.destuser is None else cm.destuser.id()
            return (id0, cm.prefs, cm.timestamp)

        for cm in q.fetch(max_len):
            yield ch_callback(cm)

    @classmethod
    def list_received(cls, user_id, max_len = 20):
        """ Query for a list of challenges issued to a particular user """
        assert user_id is not None
        if user_id is None:
            return
        k = ndb.Key(UserModel, user_id)
        # List received challenges in ascending order by timestamp (oldest first)
        q = cls.query(ChallengeModel.destuser == k).order(ChallengeModel.timestamp)

        def ch_callback(cm):
            """ Map a favorite relation into a list of users """
            p0 = cm.key.parent()
            id0 = None if p0 is None else p0.id()
            return (id0, cm.prefs, cm.timestamp)

        for cm in q.fetch(max_len):
            yield ch_callback(cm)


class ChannelModel(ndb.Model):
    """ Models connected clients receiving notifications via a Google App Engine channel """

    # Channel id (UUID)
    chid = ndb.StringProperty()

    # Type of channel: can be 'user' or 'game'
    kind = ndb.StringProperty()

    # The associated entity, either a userid or a game uuid
    entity = ndb.StringProperty()

    # The expiration time of the channel
    expiry = ndb.DateTimeProperty()

    # Is this channel presently connected?
    connected = ndb.BooleanProperty(required = False, default = False)

    # Is this channel stale (i.e. has missed updates)?
    stale = ndb.BooleanProperty(required = False, default = False)

    # The user associated with this channel
    user = ndb.KeyProperty(kind = UserModel, required = False, default = None)

    # When should the next cleanup of expired channels be done?
    _CLEANUP_INTERVAL = 30 # Minutes
    _next_cleanup = None
    _lock = threading.Lock()

    @classmethod
    def create_new(cls, kind, entity, user_id, lifetime = None):
        """ Create a new channel and return its token """
        # Every channel is assigned a random UUID
        chid = Unique.id()
        cm = cls()
        cm.chid = chid
        cm.kind = kind
        cm.entity = entity
        cm.connected = True
        cm.stale = False
        if lifetime is None:
            lifetime = timedelta(hours = 2)
            # lifetime = timedelta(minutes = 1)
        cm.expiry = datetime.utcnow() + lifetime
        cm.user = None if user_id is None else ndb.Key(UserModel, user_id)
        cm.put()
        return channel.create_channel(chid, duration_minutes = int(lifetime.total_seconds() / 60))

    @classmethod
    def disconnect(cls, chid):
        """ A channel with the given id has been disconnected """
        q = cls.query(ChannelModel.chid == chid)
        now = datetime.utcnow()
        for cm in q.fetch(1):
            if cm.expiry < now:
                # Disconnected and expired: delete it
                cm.key.delete()
            else:
                # Mark as not connected
                cm.connected = False
                cm.put()
            # If disconnecting a wait channel, notify the opponent
            if cm.kind == u"wait":
                ChannelModel.send_message(u"user", cm.entity, u'{ "kind": "challenge" }')

    @classmethod
    def connect(cls, chid):
        """ A channel with the given id is now connected """
        q = cls.query(ChannelModel.chid == chid)
        for cm in q.fetch(1):
            stale = cm.stale # Did this channel miss notifications?
            cm.stale = False
            cm.connected = True
            cm.put()
            if stale:
                channel.send_message(cm.chid, u'{ "stale": true }')

    @classmethod
    def list_connected(cls):
        """ List all presently connected users """
        CHUNK_SIZE = 500
        now = datetime.utcnow()
        # Obtain all connected channels that have not expired
        q = cls.query(ChannelModel.connected == True).filter(ChannelModel.expiry > now)
        offset = 0
        while q is not None:
            count = 0
            for cm in q.fetch(CHUNK_SIZE, offset = offset):
                if cm.user is not None:
                    # Connected channel associated with a user: return the user id
                    yield cm.user.id()
                count += 1
            if count < CHUNK_SIZE:
                break
            offset += CHUNK_SIZE

    @classmethod
    def is_connected(cls, user_id):
        """ Returns True if the given user is presently connected (online) """
        if not user_id:
            return False
        now = datetime.utcnow()
        u_key = ndb.Key(UserModel, user_id)
        # Query for all connected channels for this user that have not expired
        q = cls.query(ndb.AND(ChannelModel.connected == True, ChannelModel.user == u_key)) \
            .filter(ChannelModel.expiry > now)
        # Return True if we find at least one entity fulfilling the criteria
        return q.get(keys_only = True) != None

    @classmethod
    def exists(cls, kind, entity, user_id):
        """ Returns True if a connection with the given attributes exists """
        if not user_id:
            return False
        now = datetime.utcnow()
        u_key = ndb.Key(UserModel, user_id)
        # Query for all connected channels for this user that have not expired
        q = cls.query(ndb.AND(ChannelModel.connected == True, ChannelModel.user == u_key)) \
            .filter(ChannelModel.expiry > now) \
            .filter(ChannelModel.kind == kind) \
            .filter(ChannelModel.entity == entity)
        # Return True if we find at least one entity fulfilling the criteria
        return q.get(keys_only = True) != None

    @classmethod
    def _del_expired(cls):
        """ Delete all expired channels """
        now = datetime.utcnow()
        CHUNK_SIZE = 500
        while True:
            q = cls.query(ChannelModel.expiry < now)
            # Query and delete in chunks
            count = 0
            list_k = []
            for k in q.fetch(CHUNK_SIZE, keys_only = True):
                list_k.append(k)
                count += 1
            if count:
                ndb.delete_multi(list_k)
            if count < CHUNK_SIZE:
                # Hit end of query: We're done
                break

    @classmethod
    def send_message(cls, kind, entity, msg):
        """ Send a message to all channels matching the kind and entity """

        now = datetime.utcnow()

        with ChannelModel._lock:

            # Start by checking whether a cleanup of expired channels is due
            if cls._next_cleanup is None or (now > cls._next_cleanup):
                # Yes: do the cleanup
                cls._del_expired()
                # Schedule the next one
                cls._next_cleanup = now + timedelta(minutes = ChannelModel._CLEANUP_INTERVAL)

            CHUNK_SIZE = 50 # There are never going to be many matches for this query
            q = cls.query(ChannelModel.expiry > now).filter(
                ndb.AND(ChannelModel.kind == kind, ChannelModel.entity == entity))
            offset = 0
            while True:
                # Query and send message in chunks
                count = 0
                list_stale = []
                for cm in q.fetch(CHUNK_SIZE, offset = offset):
                    if cm.connected:
                        # Connected and listening: send the message
                        # logging.info(u"Send_message kind {0} entity {1} chid {2} msg {3}".format(kind, entity, cm.chid, msg))
                        channel.send_message(cm.chid, msg)
                    else:
                        # Channel appears to be disconnected: mark it as stale
                        cm.stale = True
                        list_stale.append(cm)
                    count += 1
                if list_stale:
                    ndb.put_multi(list_stale)
                if count < CHUNK_SIZE:
                    # Hit end of query: We're done
                    break
                offset += count


class StatsModel(ndb.Model):
    """ Models statistics about users """

    # The user associated with this statistic
    user = ndb.KeyProperty(kind = UserModel)

    # The timestamp of this statistic
    timestamp = ndb.DateTimeProperty(indexed = True, auto_now_add = True)

    games = ndb.IntegerProperty()
    human_games = ndb.IntegerProperty()

    elo = ndb.IntegerProperty(indexed = True, default = 1200)
    human_elo = ndb.IntegerProperty(indexed = True, default = 1200)

    score = ndb.IntegerProperty()
    human_score = ndb.IntegerProperty()

    score_against = ndb.IntegerProperty()
    human_score_against = ndb.IntegerProperty()

    wins = ndb.IntegerProperty()
    losses = ndb.IntegerProperty()

    human_wins = ndb.IntegerProperty()
    human_losses = ndb.IntegerProperty()

    MAX_STATS = 100


    def set_user(self, user_id):
        """ Set the user key property """
        k = None if user_id is None else ndb.Key(UserModel, user_id)
        self.user = k


    @classmethod
    def create(cls, user_id):
        """ Create a fresh instance with default values """
        sm = cls()
        sm.set_user(user_id)
        sm.elo = 1200
        sm.human_elo = 1200
        sm.games = 0
        sm.human_games = 0
        sm.score = 0
        sm.human_score = 0
        sm.score_against = 0
        sm.human_score_against = 0
        sm.wins = 0
        sm.losses = 0
        sm.human_wins = 0
        sm.human_losses = 0
        return sm


    @classmethod
    def _list_by(cls, prop, timestamp = None, max_len = MAX_STATS):
        """ Returns the Elo ratings at the indicated time point (None = now), in descending order  """
        if timestamp is None:
            timestamp = datetime.utcnow()
        # Start by finding the timestamp most closely before the given one
        q = cls.query(StatsModel.timestamp <= timestamp)
        sm = q.get()
        if sm is None:
            # No statistics available before this time point
            return
        # This is the reference timestamp we'll use
        ref_ts = sm.timestamp
        q = cls.query(StatsModel.timestamp == ref_ts).order(- prop)
        for sm in q.fetch(max_len):
            yield dict(
                user = sm.user.id(),
                games = sm.games,
                human_games = sm.human_games,
                elo = sm.elo,
                human_elo = sm.human_elo,
                score = sm.score,
                human_score = sm.human_score,
                score_against = sm.score_against,
                wins = sm.wins,
                losses = sm.losses,
                human_wins = sm.human_wins,
                human_losses = sm.human_losses
            )


    @classmethod
    def list_elo(cls, timestamp = None, max_len = MAX_STATS):
        yield cls._list_by(StatsModel.elo, timestamp, max_len)


    @classmethod
    def list_human_elo(cls, timestamp = None, max_len = MAX_STATS):
        yield cls._list_by(StatsModel.human_elo, timestamp, max_len)


    @classmethod
    def newest(cls, user_id):
        """ Returns the newest available stats record for the user """
        if user_id is None:
            return None
        k = ndb.Key(UserModel, user_id)
        q = cls.query(StatsModel.user == k).order(- StatsModel.timestamp)
        sm = q.get()
        if sm is None:
            # No stats record for the user in the database: return a default one
            sm = cls.create(user_id)
        return sm

    @staticmethod
    def put_multi(recs):
        """ Insert or update multiple stats records """
        ndb.put_multi(recs)

