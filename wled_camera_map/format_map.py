def find_grid_bounds(positions):
    smallest_x = 99999
    smallest_y = 99999
    largest_x = 0
    largest_y = 0
    for position in positions:
        if position[0] < smallest_x:
            smallest_x = position[0]
        if position[0] > largest_x:
            largest_x = position[0]
        if position[1] < smallest_y:
            smallest_y = position[1]
        if position[1] > largest_y:
            largest_y = position[1]

    width = largest_x - smallest_x + 1
    height = largest_y - smallest_y + 1
    return smallest_x, smallest_y, width, height


def convert_2d_map_to_1d(positions):
    x_offset, y_offset, width, height = find_grid_bounds(positions)

    # Create 2d list initialized to -1
    position_map = [[-1] * height for _ in range(width)]

    # Populate position map, shifting things to fit into the minimum height,width
    for i, position in enumerate(positions):
        x = position[0] - x_offset - 1
        y = position[1] - y_offset - 1
        position_map[x][y] = i

    # Turn 2d list-of-lists into 1d list for WLED
    linear_positions = [x for xs in position_map for x in xs]

    print(
        "WLED 1d array is ",
        str(len(linear_positions)),
        " LEDs long. ",
        "2D matrix is ",
        width,
        " by ",
        height,
    )
    return linear_positions, width, height


def create_wled_json(ledmap_coordinates, width, height, name):
    ledmap = {}
    ledmap["n"] = name
    ledmap["width"] = width
    ledmap["height"] = height
    ledmap["map"] = ledmap_coordinates
    return ledmap
