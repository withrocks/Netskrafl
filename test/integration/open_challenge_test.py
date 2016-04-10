# Integration tests for the open challenges.
# A running dev server needs to be available.
# Users, test001-test100, will be creating challenges.
# They are created on demand.

import logging
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class BaseIntegrationTest:
    def __init__(self):
        self.sessions = dict()
        self.root_url = "http://localhost:8080"
        self.test()

    def test(self):
        pass

    def get_session(self, email, admin=False):
        # TODO: Elos
        if email not in self.sessions:
            self.sessions[email] = self.create_login_session(email, admin)
        return self.sessions[email]

    def create_login_session(self, email, admin):
        """Logs in the user and returns a requests session

        Works only on the dev server.
        """
        session = requests.session()
        url = "{url}/_ah/login?email={email}&admin={admin}&action=Login&continue={url}".format(
            url=self.root_url, email=email, admin=admin)
        response = session.get(url)
        if response.status_code != 200:
            raise Exception("Not able to login user: {}".format(response.status_code))
        return session

    def post(self, user, resource, data=None, admin=False):
        session = self.get_session(user, admin)
        url = self.resource(resource)
        return session.post(url, data=data)

    def resource(self, res):
        return "{url}/{res}".format(url=self.root_url, res=res)


# TODO: Threaded
class OpenChallengeTest(BaseIntegrationTest):
    def test(self):
        # TODO: no_cheat should be fairplay
        challenge = {"bag_version": 1, "duration": 15, "no_cheat": 1}
        for user in map(lambda x: "test{}@example.com".format(x), xrange(100, 103)):
            response = self.post(user, "openchallenge", challenge)
            print response.status_code

    def match_all(self):
        logger.info("Triggering the matches")
        response = self.post("matchopenchallenges", "admin1@example.com", admin=True)
        print response.status_code

if __name__ == "__main__":
    logger.info("Open challenges integration test")
    test = OpenChallengeTest()

