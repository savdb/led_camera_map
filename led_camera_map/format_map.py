import json

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


def transpose(grid):
    return [list(x) for x in zip(*grid)]

def remove_empty_rows(grid):
    grid_compressed = []
    for row in grid:
        remove_row = True
        for position in row:
            if position != -1:
                remove_row = False
        if not remove_row:
            grid_compressed.append(row)
    return grid_compressed

def remove_empty_rows_and_cols(positions):
    positions = remove_empty_rows(positions)
    positions_transposed = transpose(positions)
    positions_transposed = remove_empty_rows(positions_transposed)
    positions = transpose(positions_transposed)
    return positions

def convert_2d_map_to_1d(positions):
    positions = [list(elem) for elem in positions ] # Convert to list-of-lists
    x_offset, y_offset, width, height = find_grid_bounds(positions)

    # Create 2d list initialized to -1
    position_map = [[-1] * height for _ in range(width)]

    # Populate position map
    for i, position in enumerate(positions):
        x = position[0] - 1 - x_offset
        y = position[1] - 1 - y_offset
        position_map[x][y] = i

    # Now that we have a sparse 2D array, let's remove all empty rows and columns to compress it
    compressed_positions = remove_empty_rows_and_cols(position_map)
    width = len(compressed_positions)
    height = len(compressed_positions[0])

    # Turn 2d list-of-lists into 1d list for WLED
    linear_positions = [x for xs in compressed_positions for x in xs]

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

def save_wled_json(name, ledmap, width, height):
    ledmap_json = create_wled_json(
        ledmap, width, height, name
    )

    print("Generated out/"+ name+".json")

    with open("out/"+name + ".json", "w", encoding="utf8") as outfile:
        json.dump(ledmap_json, outfile, separators=(',',':'))

    return ledmap_json
