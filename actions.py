from exceptions import InvalidAction
from utils import is_coordinate, inside_rectangle


class Action:
    def __init__(self, unit_id):
        if not isinstance(unit_id, int):
            raise InvalidAction('Unit id must be an integer')

        self.unit_id = unit_id

    def apply(self, game):
        pass

    def validate(self, game):
        pass


class Move(Action):
    def __init__(self, unit_id, x, y):
        super().__init__(unit_id)
        self.target = (x, y)
        if not is_coordinate(self.target):
            raise InvalidAction('Move target must be coordinate (tuple of two integers)')

    def apply(self, game, busy_positions=None):
        unit = game.get_unit_by_id(self.unit_id)
        if busy_positions is not None:
            if self.target in busy_positions:
                return

        unit.position = self.target

    def validate(self, game):
        unit = game.get_unit_by_id(self.unit_id)
        if unit is None:
            return False

        unit_x, unit_y = unit.position
        target_x, target_y = self.target

        return (inside_rectangle(game.width, game.height, target_x, target_y)
                and abs(target_x - unit_x) <= 1
                and abs(target_y - unit_y) <= 1)


class Teleport(Action):
    def apply(self, game, busy_positions=None):
        unit = game.get_unit_by_id(self.unit_id)
        if busy_positions is not None:
            if unit.spawn in busy_positions:
                return

        unit.position = unit.spawn

    def validate(self, game):
        unit = game.get_unit_by_id(self.unit_id)
        return unit is not None


class Fire(Action):
    def __init__(self, unit_id, x, y):
        super().__init__(unit_id)
        self.target = (x, y)
        if not is_coordinate(self.target):
            raise InvalidAction('Fire target must be coordinate (tuple of two integers)')

    def apply(self, game):
        game.remove_unit_at(self.target)

    def validate(self, game):
        unit = game.get_unit_by_id(self.unit_id)
        if unit is None:
            return False

        unit_x, unit_y = unit.position
        target_x, target_y = self.target

        return (inside_rectangle(game.width, game.height, target_x, target_y)
                and abs(target_x - unit_x) <= 2
                and abs(target_y - unit_y) <= 2)


def parse_action(command):
    try:
        action_name = command['action']
    except (KeyError, TypeError):
        raise InvalidAction('Undefined action')

    try:
        action_cls = ACTION_CLASSES[action_name]
    except KeyError:
        raise InvalidAction('Unknown action')

    try:
        action_properties = command['properties']
    except KeyError:
        raise InvalidAction('Undefined properties')

    try:
        action = action_cls(**action_properties)
    except:
        raise InvalidAction('Wrong properties')

    return action


ACTION_CLASSES = {
    'teleport': Teleport,
    'move': Move,
    'fire': Fire
}