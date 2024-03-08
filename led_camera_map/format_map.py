import json


def flatten_2d_map(positions: list[tuple[int, int]]):
    # This method also removes all empty rows or columns to compress the grid
    rows = set()
    cols = set()
    mymap = dict()
    for i, (x, y) in enumerate(positions):
        rows.add(y)
        cols.add(x)
        col = mymap.get(x, dict())
        col[y] = i
        mymap[x] = col
    values = []
    for col in sorted(list(cols)):
        for row in sorted(list(rows)):
            values.append(mymap.get(col, dict()).get(row, -1))
    width = len(cols)
    height = len(rows)

    print(
        "WLED 1d array is ",
        str(len(values)),
        " LEDs long. ",
        "2D matrix is ",
        width,
        " by ",
        height,
    )
    return values, width, height


def create_wled_json(ledmap_coordinates, width, height, name):
    ledmap = {}
    ledmap["n"] = name
    ledmap["width"] = width
    ledmap["height"] = height
    ledmap["map"] = ledmap_coordinates

    return ledmap


def save_wled_json(name, ledmap, width, height):
    ledmap_json = create_wled_json(ledmap, width, height, name)

    print("Generated out/" + name + ".json")

    with open("out/" + name + ".json", "w", encoding="utf8") as outfile:
        json.dump(ledmap_json, outfile, separators=(",", ":"))

    return ledmap_json


def visualize_ledmap(ledmap_json):
    width = ledmap_json["width"]
    ledmap = ledmap_json["map"]
    ledmap[:] = [str(x) if x != -1 else "." for x in ledmap]  # Replace all "-1"

    column_width = 4  # How many characters wide each printed column is

    n = int(len(ledmap) / width)
    pat = "{{:{}}}".format(column_width)
    line = "\n".join(pat * width for _ in range(n))
    formatted_map = line.format(*ledmap)
    print(ledmap_json["n"], "looks like:")
    print(formatted_map)

    with open("out/map_visualization.txt", "w", encoding="utf-8") as text_file:
        text_file.write(formatted_map)
