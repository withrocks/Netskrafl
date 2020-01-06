import unittest
from google.appengine.api import memcache
from google.appengine.ext import ndb
from fixtures import * 
import netskrafl


def test_create_open_challenge_adds_memcache_entry(client, user):
    resp = client.post("/openchallenge")
    assert resp.status_code == 200


