"""Tests for constants.py"""

import unittest

from mundane import constants


class SecondsPerDayTest(unittest.TestCase):

    def test_value(self):
        self.assertEqual(24 * 60 * 60, constants.SECONDS_PER_DAY)

    def test_type(self):
        self.assertIs(type(constants.SECONDS_PER_DAY), int)
