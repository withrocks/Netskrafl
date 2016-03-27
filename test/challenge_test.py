# TODO: Change the setup so that dependencies can be imported from
# a package (netskrafl):
#from netskrafl.challenge import ChallengeService
from challenge import ChallengeService, Challenge
from unittest import TestCase


class TestChallengeService(TestCase):
    def test_can_create_challenge(self):
        challenge = Challenge(player_id=1, player_rating=1200, duration=15,
                              bag_version=1, no_cheat=True)
        challenge_svc = ChallengeService()
        challenge_svc.add_challenge(challenge)


