import unittest
from game import Game
from actions import Move, Fire, Teleport, Action, create_action, ACTION_CLASSES
from exceptions import InvalidAction


class InGameActionValidationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}]
        ]
        cls.game = Game(10, 10, teams)

    def test_fire_outside_map(self):
        with self.assertRaises(InvalidAction):
            Fire(0, -1, -1, self.game)

    def test_fire_outside_range(self):
        with self.assertRaises(InvalidAction):
            Fire(0, 3, 3, self.game)

    def test_move_outside_map(self):
        with self.assertRaises(InvalidAction):
            Move(0, -1, -1, self.game)

    def test_move_outside_range(self):
        with self.assertRaises(InvalidAction):
            Move(0, 2, 2, self.game)

    def test_non_existent_unit_action(self):
        with self.assertRaises(InvalidAction):
            Action(5, self.game)


class JSONActionParsingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}]
        ]
        cls.game = Game(10, 10, teams)

    def test_undefined_action(self):
        with self.assertRaises(InvalidAction):
            create_action({}, self.game)

    def test_unknown_action(self):
        data = {'action': 'fly_me_to_the_mars'}
        with self.assertRaises(InvalidAction):
            create_action(data, self.game)

    def test_wrong_properties(self):
        data = {
            'action': 'move',
            'properties': {'wrong': 'property'}
        }
        with self.assertRaises(InvalidAction):
            create_action(data, self.game)

    def test_not_a_json_format(self):
        with self.assertRaises(InvalidAction):
            create_action(1, self.game)
