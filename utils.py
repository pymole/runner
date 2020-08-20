def is_coordinate(coord):
    return (isinstance(coord, tuple)
            and len(coord) == 2
            and isinstance(coord[0], int)
            and isinstance(coord[1], int))


def inside_rectangle(width, height, x, y):
    return 0 <= x < width and 0 <= y < height