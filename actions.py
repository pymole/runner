from exceptions import InvalidAction
from utils import is_coordinate, inside_rectangle


# TODO rename fire to shot

class Action:
    def __init__(self, unit_id, game):
        if not isinstance(unit_id, int):
            raise InvalidAction('Unit id must be an integer')

        self.unit = game.get_unit_by_id(unit_id)
        if self.unit is None:
            raise InvalidAction('Non-existent unit')

        self.game = game
        self.validate()

    def apply(self):
        raise NotImplemented

    def validate(self):
        raise NotImplemented

    def render(self):
        raise NotImplemented


class Move(Action):
    def __init__(self, unit_id, x, y, game):
        self.target = (x, y)
        super().__init__(unit_id, game)

    def apply(self, busy_positions=None):
        if busy_positions is not None:
            if self.target in busy_positions:
                return

        self.unit.position = self.target

    def validate(self):
        if not is_coordinate(self.target):
            raise InvalidAction('Move target must be coordinate (tuple of two integers)')

        target_x, target_y = self.target
        if not inside_rectangle(self.game.width, self.game.height, target_x, target_y):
            raise InvalidAction('Move outside the map')

        unit_x, unit_y = self.unit.position
        if abs(target_x - unit_x) > 1 or abs(target_y - unit_y) > 1:
            raise InvalidAction('Out of range move')

    def render(self):
        return {
            "action": "move",
            "properties": {
                "unit_id": self.unit.id,
                "x": self.target[0],
                "y": self.target[1]
            }
        }


# TODO resolve super conflict of __init__ and validate of move and teleport
class Teleport(Move):
    def __init__(self, unit_id, game):
        super(Action, self).__init__(unit_id, game)
        self.target = self.unit.position

    def validate(self):
        if not is_coordinate(self.target):
            raise InvalidAction('Move target must be coordinate (tuple of two integers)')

    def render(self):
        return {
            "action": "teleport",
            "properties": {
                "unit_id": self.unit.id,
            }
        }


class Fire(Action):
    def __init__(self, unit_id, x, y, game):
        self.target = (x, y)
        super().__init__(unit_id, game)

    def apply(self):
        self.game.remove_unit_at(self.target)

    def validate(self):
        if not is_coordinate(self.target):
            raise InvalidAction('Fire target must be coordinate (tuple of two integers)')

        target_x, target_y = self.target
        if not inside_rectangle(self.game.width, self.game.height, target_x, target_y):
            raise InvalidAction('Fire outside the map')

        unit_x, unit_y = self.unit.position
        if abs(target_x - unit_x) > 2 or abs(target_y - unit_y) > 2:
            raise InvalidAction('Out of range fire')

    def render(self):
        return {
            "action": "fire",
            "properties": {
                "unit_id": self.unit.id,
                "x": self.target[0],
                "y": self.target[1]
            }
        }


# TODO maybe pass it to Game class
def create_action(game, command):
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
        action = action_cls(**action_properties, game=game)
    except:
        raise InvalidAction('Wrong properties')

    return action


def split_actions(actions):
    # split actions on moves and fire
    move_actions = []
    fire_actions = []

    for action in actions:
        if isinstance(action, Fire):
            fire_actions.append(action)
        else:
            move_actions.append(action)

    return move_actions, fire_actions


ACTION_CLASSES = {
    'teleport': Teleport,
    'move': Move,
    'fire': Fire
}