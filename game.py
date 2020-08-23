from itertools import chain
from collections import defaultdict, Counter
import json

from exceptions import InitializationError, InvalidAction
from utils import is_coordinate, inside_rectangle
from actions import Fire, create_action, split_actions


class Game:
    __slots__ = ('width', 'height', 'units', 'ticks', 'team_count', 'remaining_teams',
                 'map_config', 'log')

    def __init__(self, width, height, teams):
        self.width = width
        self.height = height

        self.units = self.validate_teams(teams)
        self.remaining_teams = set(range(len(teams)))

        self.map_config = {
            'map_width': self.width,
            'map_height': self.height,
            'units': [
                {'id': unit.id, 'spawn_x': unit.spawn[0], 'spawn_y': unit.spawn[1], 'team': unit.team}
                for unit in self.units.values()
            ]
        }

        self.log = []

    def validate_teams(self, teams):
        # TODO spawns
        if not isinstance(teams, list):
            raise InitializationError('"teams" must be a list.')
        if len(teams) == 0:
            raise InitializationError('Empty "teams"')

        unit_positions = set()
        spawn_positions = set()
        units = {}

        for team_id, team in enumerate(teams):
            for unit in team:
                try:
                    unit_id = unit['id']
                except KeyError:
                    raise InitializationError('Undefined unit id')

                if not isinstance(unit_id, int):
                    raise InitializationError('Unit ID must be an integer')
                if unit_id in units:
                    raise InitializationError('Unit ID must be unique')

                try:
                    spawn_x = unit['spawn_x']
                    spawn_y = unit['spawn_y']
                except KeyError:
                    raise InitializationError('Undefined spawn coordinates')
                else:
                    spawn = (spawn_x, spawn_y)

                if not is_coordinate(spawn):
                    raise InitializationError('Spawn not a coordinate')
                if spawn in spawn_positions:
                    raise InitializationError('Spawn positions of the units must be unique')
                if not inside_rectangle(self.width, self.height, *spawn):
                    raise InitializationError('Spawn position must be inside a game field')

                try:
                    position_x = unit['position_x']
                    position_y = unit['position_y']
                except KeyError:
                    position = spawn
                else:
                    position = (position_x, position_y)

                    if not is_coordinate(position):
                        raise InitializationError('Position not a coordinate')
                    if position in unit_positions:
                        raise InitializationError('Position of the unit must be unique')
                    if not inside_rectangle(self.width, self.height, *spawn):
                        raise InitializationError('Position of units must be inside a game field')

                units[unit_id] = Unit(unit_id, team_id, spawn, position)
                spawn_positions.add(spawn)
                unit_positions.add(position)

        # TODO think about this commented code. Need I check this?
        # if set(units.keys()) - set(range(len(units))):
        #     raise InvalidUnits('Unit ids should be consecutive starting from zero (0, 1, 2, ...)')

        return units

    @classmethod
    def from_map_config(cls, config):
        try:
            width = config['map_width']
            height = config['map_height']
        except KeyError:
            raise InitializationError('Undefined map size')

        try:
            teams = config['teams']
        except KeyError:
            raise InitializationError('Undefined "teams"')

        return Game(width, height, teams)

    def __str__(self):
        field = [['-' for _ in range(self.width)] for _ in range(self.height)]
        for unit in self.units.values():
            pos_x, pos_y = unit.position
            spawn_x, spawn_y = unit.spawn
            field[spawn_y][spawn_x] = 'X' + str(unit.id)
            field[pos_y][pos_x] = str(unit.team) + str(unit.id)

        return '\n'.join('\t'.join(row) for row in field)

    def __len__(self):
        return len(self.log)

    def tick(self, team_commands):
        actions = self.validate_commands(team_commands)
        move_actions, fire_actions = split_actions(actions)
        busy_positions, non_conflict_moves = self.resolve_move_conflicts(move_actions)

        for move_action in non_conflict_moves:
            move_action.apply(busy_positions)

        dead_units = self.spawn_kills()
        # dead units can't fire
        fire_actions = [action for action in fire_actions if action.unit not in dead_units]

        self.fire(fire_actions)
        self.refresh_remaining_teams()

        tick_log = {
            'units': [unit.render_state() for unit in self.units.values()],
            'actions': [action.render() for action in chain(non_conflict_moves, fire_actions)]
        }

        self.log.append(tick_log)

    def validate_commands(self, team_commands):
        valid_actions = []
        for team, command in team_commands.items():
            for action in command:
                # action of non-existent unit is invalid
                try:
                    action = create_action(self, action)
                except InvalidAction:
                    continue

                # can do actions only for units of my team
                if action.unit.team == team:
                    valid_actions.append(action)

        return valid_actions

    def resolve_move_conflicts(self, move_actions):
        # the unit performs an action if no one else moves to the target
        # and target is free cell or will be free after moves
        target_moves = defaultdict(list)
        for move_action in move_actions:
            target_moves[move_action.target].append(move_action)

        non_conflict_moves = [moves[0] for moves in target_moves.values() if len(moves) == 1]
        # units with the same target do not move
        is_not_moving = set(self.units.values()) - set(move.unit for move in non_conflict_moves)

        busy_positions = {unit.position for unit in is_not_moving}

        return busy_positions, non_conflict_moves

    def spawn_kills(self):
        dead_units_ids = []
        for killer in self.units.values():
            killer_x, killer_y = killer.position

            for victim in self.units.values():
                if victim.team == killer.team:
                    continue

                spawn_x, spawn_y = victim.spawn
                if abs(spawn_x - killer_x) + abs(spawn_y - killer_y) <= 1:
                    dead_units_ids.append(victim.id)

        dead_units = {self.units.pop(unit_id) for unit_id in dead_units_ids}
        return dead_units

    def fire(self, fire_actions):
        for fire_action in fire_actions:
            fire_action.apply()

    def refresh_remaining_teams(self):
        self.remaining_teams = {unit.team for unit in self.units.values()}

    def get_unit_by_id(self, unit_id):
        return self.units.get(unit_id, None)

    def remove_unit_at(self, position):
        for unit in self.units.values():
            if unit.position == position:
                self.units.pop(unit.id)
                break

    def get_winners(self):
        # count units in teams
        units_in_team = Counter(unit.team for unit in self.units.values())

        # get teams with maximal unit count
        winner_teams = []
        max_size = 0
        for team_id, team_size in units_in_team.items():
            if max_size > team_size:
                continue
            if max_size < team_size:
                winner_teams.clear()
                max_size = team_size

            winner_teams.append(team_id)

        return winner_teams

    def get_current_state(self):
        return self.log[-1]

    def get_map_config(self, from_perspective):
        return {**self.map_config, 'my_team_id': from_perspective}

    def save_log(self, path):
        with open(path, 'w') as f:
            json.dump(self.log, f)

    def is_ended(self):
        return False


class Unit:
    __slots__ = ('id', 'team', 'position', 'spawn')

    def __init__(self, id, team, spawn, position):
        self.id = id
        self.team = team
        self.position = position
        self.spawn = spawn

    def render_state(self):
        return {
            'id': self.id,
            'x': self.position[0],
            'y': self.position[1]
        }
