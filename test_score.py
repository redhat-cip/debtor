#
# Copyright (C) 2015 Red Hat Inc.
#
# Author: Frederic Lepied <frederic.lepied@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import unittest

import score


class TestScore(unittest.TestCase):

    def test_score_review_none(self):
        self.assertEqual(
            score.score_review('{"type": "stats", "status": "NONE"}',
                               'patch', ()), 200)

    def test_score_review_exception(self):
        self.assertEqual(
            score.score_review('{"type": "stats", "status": "NONE"}',
                               'patch', ('patch')), 50)

    def test_score_review_new(self):
        self.assertEqual(
            score.score_review(
                '{"status":"NEW","id":"id",'
                '"patchSets":[{"approvals":[{"type": "verified"}]}]}',
                'patch', ()), 20)

    def test_score_review_merged(self):
        self.assertEqual(
            score.score_review(
                '{"status":"MERGED","id":"id"}',
                'patch', ()), 10)

    def test_score_review_abandoned(self):
        self.assertEqual(
            score.score_review(
                '{"status":"ABANDONED","id":"id",'
                '"patchSets":[{"approvals":[{"type": "verified"}]}]}',
                'patch', ()), 150)

    def test_score_review_cherry(self):
        self.assertEqual(
            score.score_review(
                '{"status":"CHERRY","id":"id"}',
                'patch', ()), 10)

    def test_score_review_unknown(self):
        self.assertEqual(
            score.score_review(
                '{"status":"UNKNOWN","id":"id"}',
                'patch', ()), 200)

    def test_score_review_no_jenkins(self):
        self.assertEqual(
            score.score_review(
                '{"status":"NEW","id":"id",'
                '"patchSets":[{"approvals":'
                '[{"type": "Verified","by": {"username":"jenkins"},'
                '"value": "-1"}]}]}',
                'patch', ()), 70)

    def test_score_review_negative1_vote(self):
        self.assertEqual(
            score.score_review(
                '{"status":"NEW","id":"id",'
                '"patchSets":[{"approvals":'
                '[{"type": "Code-Review",'
                '"value": "-1"}]}]}',
                'patch', ()), 70)

    def test_score_review_negative2_vote(self):
        self.assertEqual(
            score.score_review(
                '{"status":"NEW","id":"id",'
                '"patchSets":[{"approvals":'
                '[{"type": "Code-Review",'
                '"value": "-2"}]}]}',
                'patch', ()), 120)

    def test_score_review_positive_vote(self):
        self.assertEqual(
            score.score_review(
                '{"status":"NEW","id":"id",'
                '"patchSets":[{"approvals":'
                '[{"type": "Code-Review",'
                '"value": "+1"}]}]}',
                'patch', ()), 15)

    def test_score_review_positive2_vote(self):
        self.assertEqual(
            score.score_review(
                '{"status":"NEW","id":"id",'
                '"patchSets":[{"approvals":'
                '[{"type": "Code-Review",'
                '"value": "+2"}]}]}',
                'patch', ()), 10)

    def test_score_interdiff(self):
        self.assertEqual(
            score.score_interdiff(['', '0,0,0'], 'patch'),
            0)

    def test_score_interdiff_small(self):
        self.assertEqual(
            score.score_interdiff(['', '1,0,0'], 'patch'),
            10)

    def test_score_interdiff_big(self):
        self.assertEqual(
            score.score_interdiff(['', '26,0,0'], 'patch'),
            100)

if __name__ == "__main__":
    unittest.main()

# test_score.py ends here
