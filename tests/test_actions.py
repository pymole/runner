import unittest
from game import Game
from actions import Move, Fire, Teleport, parse_action, ACTION_CLASSES
from exceptions import InvalidAction


class ActionValidationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}]
        ]
        cls.game = Game(10, 10, teams)

    def test_fire_outside_map(self):
        is_valid = Fire(0, -1, -1).validate(self.game)
        self.assertFalse(is_valid)

    def test_fire_outside_range(self):
        is_valid = Fire(0, 3, 3).validate(self.game)
        self.assertFalse(is_valid)

    def test_fire_valid_range(self):
        is_valid = Fire(0, 2, 2).validate(self.game)
        self.assertTrue(is_valid)

    def test_non_existent_unit_firing(self):
        is_valid = Fire(5, 2, 2).validate(self.game)
        self.assertFalse(is_valid)

    def test_move_outside_map(self):
        is_valid = Move(0, -1, -1).validate(self.game)
        self.assertFalse(is_valid)

    def test_move_outside_range(self):
        is_valid = Move(0, 2, 2).validate(self.game)
        self.assertFalse(is_valid)

    def test_move_valid(self):
        is_valid = Move(0, 1, 1).validate(self.game)
        self.assertTrue(is_valid)

    def test_non_existent_unit_move(self):
        is_valid = Move(5, 5, 5).validate(self.game)
        self.assertFalse(is_valid)


class ActionParsingTestCase(unittest.TestCase):
    def test_undefined_action(self):
        with self.assertRaises(InvalidAction):
            parse_action({})

    def test_unknown_action(self):
        data = {'action': 'fly_me_to_the_mars'}
        with self.assertRaises(InvalidAction):
            parse_action(data)

    def test_wrong_properties(self):
        data = {
            'action': None,
            'properties': {'wrong': 'property'}
        }

        for action_name in ACTION_CLASSES.keys():
            data['action'] = action_name
            with self.subTest(data=data):
                with self.assertRaises(InvalidAction):
                    parse_action(data)

    def test_unsupported_data_format(self):
        with self.assertRaises(InvalidAction):
            parse_action(1)
