import random
import json


directions = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
]


class Unit:
    def __init__(self, id, spawn_x, spawn_y, team):
        self.id = id
        self.team = team
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.x = spawn_x
        self.y = spawn_y

    def update(self, x, y):
        self.x = x
        self.y = y


def on_map(x, y, map_width, map_height):
    return 0 <= x < map_width and 0 <= y < map_height


def random_move(unit, map_width, map_height):
    while True:
        dir_x, dir_y = random.choice(directions)
        new_x = unit.x + dir_x
        new_y = unit.y + dir_y

        if on_map(new_x, new_y, map_width, map_height):
            break

    return new_x, new_y


def main():
    config = json.loads(input())
    # there begins first turn

    my_team_id = config['my_team_id']
    map_width = config['map_width']
    map_height = config['map_height']

    units = {unit['id']: Unit(**unit) for unit in config['units']}

    while True:
        # get tick info
        tick = json.loads(input())

        # update local game state
        for unit in tick['units']:
            units[unit['id']].update(unit['x'], unit['y'])

        # make random moves for my units
        command = []
        for unit in units.values():
            if unit.team == my_team_id:
                move_x, move_y = random_move(unit, map_width, map_height)
                action = {
                    'action': 'move',
                    'properties': {'unit_id': unit.id, 'x': move_x, 'y': move_y}
                }
                command.append(action)

        command = json.dumps(command)

        print(command)


if __name__ == '__main__':
    main()
