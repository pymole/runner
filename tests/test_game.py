from game import Game, Unit
from actions import Teleport, Move, Fire
import unittest


class TeamActionsFilteringTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}],
            [{"id": 1, "spawn_x": 9, "spawn_y": 9}]
        ]
        cls.game = Game(10, 10, teams)

    def test_non_existent_team_move(self):
        team_actions = {2: [Teleport(0)]}

        valid_actions = self.game.filter_team_actions(team_actions)
        self.assertEqual(len(valid_actions), 0)

    def test_different_team_move(self):
        team_actions = {0: [Teleport(1)]}

        valid_actions = self.game.filter_team_actions(team_actions)
        self.assertEqual(len(valid_actions), 0)

    def test_non_existent_unit_move(self):
        team_actions = {0: [Teleport(2)]}

        valid_actions = self.game.filter_team_actions(team_actions)
        self.assertEqual(len(valid_actions), 0)

    def test_valid_move(self):
        team_actions = {0: [Teleport(0)]}

        valid_actions = self.game.filter_team_actions(team_actions)
        self.assertEqual(len(valid_actions), 1)


class ActionsSplitTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}],
            [{"id": 1, "spawn_x": 9, "spawn_y": 9}]
        ]
        cls.game = Game(10, 10, teams)

    def test_all_valid_split(self):
        actions = [
            Teleport(0),
            Move(0, 1, 1),
            Fire(1, 7, 7),
        ]

        moves, fires = self.game.validate_and_split_actions(actions)
        self.assertEqual(len(moves), 2)
        self.assertEqual(len(fires), 1)

    def test_some_invalid_actions(self):
        actions = [
            Teleport(0),
            Move(0, 3, 3),
            Fire(1, -1, 0),
        ]

        moves, fires = self.game.validate_and_split_actions(actions)
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(fires), 0)


class SpawnKillsTestCase(unittest.TestCase):
    def test_kill_spawn(self):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}],
            [{"id": 1, "spawn_x": 9, "spawn_y": 9, "position_x": 1, "position_y": 0}]
        ]
        game = Game(10, 10, teams)
        game.spawn_kills()

        self.assertTrue(1 in game.units)
        self.assertFalse(0 in game.units)

    def test_team_kill(self):
        teams = [
            [
                {"id": 0, "spawn_x": 0, "spawn_y": 0},
                {"id": 1, "spawn_x": 4, "spawn_y": 4, "position_x": 1, "position_y": 0}
            ]
        ]
        game = Game(10, 10, teams)
        game.spawn_kills()

        self.assertTrue(0 in game.units)
        self.assertTrue(1 in game.units)

    def test_simultaneous_kill(self):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0, "position_x": 3, "position_y": 4}],
            [{"id": 1, "spawn_x": 4, "spawn_y": 4, "position_x": 1, "position_y": 0}]
        ]
        game = Game(10, 10, teams)
        game.spawn_kills()

        self.assertEqual(len(game.units), 0)


class FireTestCase(unittest.TestCase):
    def test_single_fire(self):
        actions = [Fire(0, 2, 2)]
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}],
            [{"id": 1, "spawn_x": 2, "spawn_y": 2}]
        ]
        game = Game(10, 10, teams)
        game.fire(actions)

        self.assertTrue(0 in game.units)
        self.assertFalse(1 in game.units)

    def test_simultaneous_fire(self):
        actions = [Fire(0, 2, 2), Fire(1, 0, 0)]
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}],
            [{"id": 1, "spawn_x": 2, "spawn_y": 2}]
        ]
        game = Game(10, 10, teams)
        game.fire(actions)

        self.assertEqual(len(game.units), 0)


class MoveConflictResolution(unittest.TestCase):
    def test_free_move(self):
        teams = [
            [{"id": 0, "spawn_x": 1, "spawn_y": 1}],
        ]
        for move in [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0)]:
            with self.subTest(move=move):
                game = Game(10, 10, teams)

                actions = [Move(0, *move)]
                game.resolve_move_conflicts(actions)

                self.assertEqual(game.get_unit_by_id(0).position, move)

    def test_same_target_move(self):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}],
            [{"id": 1, "spawn_x": 2, "spawn_y": 2}]
        ]
        game = Game(10, 10, teams)

        actions = [Move(0, 1, 1), Move(1, 1, 1)]
        game.resolve_move_conflicts(actions)

        self.assertEqual(game.get_unit_by_id(0).position, (0, 0))
        self.assertEqual(game.get_unit_by_id(1).position, (2, 2))

    def test_position_swap(self):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}],
            [{"id": 1, "spawn_x": 1, "spawn_y": 1}]
        ]
        game = Game(10, 10, teams)

        actions = [Move(0, 1, 1), Move(1, 0, 0)]
        game.resolve_move_conflicts(actions)

        self.assertEqual(game.get_unit_by_id(0).position, (1, 1))
        self.assertEqual(game.get_unit_by_id(1).position, (0, 0))

    def test_blocked_swap(self):
        teams = [
            [{"id": 0, "spawn_x": 0, "spawn_y": 0}],
            [
                {"id": 1, "spawn_x": 4, "spawn_y": 4, "position_x": 1, "position_y": 0},
                {"id": 2, "spawn_x": 5, "spawn_y": 5, "position_x": 0, "position_y": 1}
            ]
        ]
        game = Game(10, 10, teams)

        actions = [Move(0, 1, 0), Move(1, 0, 1), Move(2, 1, 0)]
        game.resolve_move_conflicts(actions)

        self.assertEqual(game.get_unit_by_id(0).position, (0, 0))
        self.assertEqual(game.get_unit_by_id(1).position, (1, 0))
        self.assertEqual(game.get_unit_by_id(2).position, (0, 1))
    # TODO test Teleports
