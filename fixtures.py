import pytest
from google.appengine.ext import ndb
from google.appengine.ext import testbed

# We do this here for a specific reason: We can not import e.g. netskrafl
# since it uses GAE without first stubbing. If we ensure that we have
# the GAE testbed ready here and then import fixtures at the top of the
# testrunner, we can import netskrafl on module level without issues in the tests.
testbed = testbed.Testbed()
testbed.activate()

testbed.init_datastore_v3_stub()
testbed.init_memcache_stub()
testbed.init_app_identity_stub()
testbed.init_user_stub()

@pytest.fixture()
def client():
    import netskrafl
    with netskrafl.app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def gae_cleanup():
    yield
    # Clear ndb's in-context cache between tests.
    # This prevents data from leaking between tests.
    # Alternatively, you could disable caching by
    # using ndb.get_context().set_cache_policy(False)
    ndb.get_context().clear_cache()

def create_user(email='user@example.com', id='123', is_admin=False):
    testbed.setup_env(
        user_email=email,
        user_id=id,
        user_is_admin='1' if is_admin else '0',
        overwrite=True)

@pytest.fixture()
def user():
    return create_user()


