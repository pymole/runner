from collections import defaultdict, Counter
from exceptions import InitializationError
from utils import is_coordinate, inside_rectangle


class Game:
    __slots__ = ('width', 'height', 'units', 'ticks', 'team_count', 'remaining_teams')

    def __init__(self, width, height, teams):
        self.width = width
        self.height = height

        self.units = self.validate_teams(teams)
        self.remaining_teams = set(range(len(teams)))
        self.ticks = 0

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

                units[unit_id] = Unit(team_id, spawn, position)
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
        for unit_id, unit in self.units.items():
            pos_x, pos_y = unit.position
            spawn_x, spawn_y = unit.spawn
            field[spawn_y][spawn_x] = 'X' + str(unit_id)
            field[pos_y][pos_x] = str(unit.team) + str(unit_id)

        return '\n'.join('\t'.join(row) for row in field)

    def tick(self, team_actions):
        """One game tick"""
        actions = self.filter_team_actions(team_actions)
        move_actions, fire_actions = self.validate_and_split_actions(actions)
        self.resolve_move_conflicts(move_actions)
        dead_ids = self.spawn_kills()
        # dead units can't fire
        fire_actions = [action for action in fire_actions if action.unit_id not in dead_ids]
        self.fire(fire_actions)
        self.refresh_remaining_teams()

        self.ticks += 1

    def filter_team_actions(self, team_actions):
        valid_actions = []
        for team, actions in team_actions.items():
            for action in actions:
                # action of non-existent unit is invalid
                try:
                    unit = self.units[action.unit_id]
                except KeyError:
                    continue

                # can do actions only for units of my team
                if unit.team == team:
                    valid_actions.append(action)

        return valid_actions

    def validate_and_split_actions(self, actions):
        # filter invalid moves and get groups of actions
        move_actions = []
        fire_actions = []

        for action in actions:
            is_valid = action.validate(self)
            if is_valid:
                if isinstance(action, Fire):
                    fire_actions.append(action)
                else:
                    move_actions.append(action)

        return move_actions, fire_actions

    def resolve_move_conflicts(self, move_actions):
        # the unit performs an action if no one else moves to the target
        # and target is free cell or will be free after moves
        # TODO teleport fix
        target_moves = defaultdict(list)
        for move_action in move_actions:
            target_moves[move_action.target].append(move_action)

        non_conflict_moves = [moves[0] for moves in target_moves.values() if len(moves) == 1]
        # units with the same target do not move
        is_not_moving = set(self.units.keys()) - set(move.unit_id for move in non_conflict_moves)

        busy_positions = {self.units[unit_id].position for unit_id in is_not_moving}
        for move_action in non_conflict_moves:
            move_action.apply(self, busy_positions)

    def spawn_kills(self):
        dead_units_ids = set()
        for killer_id, killer in self.units.items():
            killer_x, killer_y = killer.position

            for victim_id, victim in self.units.items():
                if victim.team == killer.team:
                    continue

                spawn_x, spawn_y = victim.spawn
                if abs(spawn_x - killer_x) + abs(spawn_y - killer_y) <= 1:
                    dead_units_ids.add(victim_id)

        for unit_id in dead_units_ids:
            self.units.pop(unit_id)

        return dead_units_ids

    def fire(self, fire_actions):
        for fire_action in fire_actions:
            fire_action.apply(self)

    def get_unit_by_id(self, unit_id):
        return self.units.get(unit_id, None)

    def remove_unit_at(self, position):
        for unit_id, unit in self.units.items():
            if unit.position == position:
                self.units.pop(unit_id)
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

    def refresh_remaining_teams(self):
        self.remaining_teams = {unit.team for unit in self.units.values()}

    def get_state(self):
        return {
            'tick': self.ticks,
            'units': [
                {'id': unit_id, 'x': unit.position[0], 'y': unit.position[1]}
                for unit_id, unit in self.units.items()
            ]
        }

    def get_map_config(self, from_perspective):
        return {
            'my_team_id': from_perspective,
            'map_width': self.width,
            'map_height': self.height,
            'units': [
                {'id': unit_id, 'spawn_x': unit.spawn[0], 'spawn_y': unit.spawn[1], 'team': unit.team}
                for unit_id, unit in self.units.items()
            ]
        }

    def is_ended(self):
        return False


class Unit:
    __slots__ = ('team', 'position', 'spawn')

    def __init__(self, team, spawn, position):
        self.team = team
        self.position = position
        self.spawn = spawn




from actions import Fire
