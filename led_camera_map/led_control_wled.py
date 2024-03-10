import json
import time
import requests


def get_full_info(wled_ip):
    info_response = requests.get(f"http://{wled_ip}/json/info", timeout=5)
    return json.loads(info_response.text)


def get_full_state(wled_ip):
    state_response = requests.get(f"http://{wled_ip}/json/state", timeout=5)
    return json.loads(state_response.text)


def get_led_count(wled_ip):
    info = get_full_info(wled_ip)
    num_leds = info["leds"]["countP"]
    assert isinstance(num_leds, int)
    return num_leds


def set_current_ledmap_to_name(wled_ip, ledmap_name):
    info = get_full_info(wled_ip)
    ledmap_id = 0

    for ledmap in info["maps"]:
        if "n" in ledmap and ledmap["n"] in (ledmap_name, ledmap_name + ".json"):
            ledmap_id = ledmap["id"]

    set_current_ledmap_to_id(wled_ip, ledmap_id)

    return ledmap_id

def set_current_ledmap_to_id(wled_ip, ledmap_id):
    print("Setting LEDMap to id", str(ledmap_id))
    state = {}
    state["ledmap"] = ledmap_id
    response = requests.post(
        f"http://{wled_ip}/json/state", data=json.dumps(state), timeout=5
    )
    print("Set LEDmap response ", response.text)

def upload_ledmap(wled_ip, ledmap_name):
    print("Uploading ledmap to " + wled_ip)

    files = {
        "data": (
            "/" + ledmap_name + ".json",  # WLED requires filename to start with /
            open("out/" + ledmap_name + ".json", "rb"),  # Json was written to a file
            "text/json",
            {
                "Content-Type": "text/json",
                "Content-Disposition": 'form-data; name="data"; filename="/'
                + ledmap_name
                + '.json"',
            },
        )
    }

    response = requests.post(f"http://{wled_ip}/edit", files=files, timeout=5)

    print("Upload response ", response.text)
    assert response.status_code == 200
    return response


def reboot_wled(wled_ip):
    print("Wait up to 30 seconds for WLED to reboot...")
    requests.get(f"http://{wled_ip}/reset", timeout=5)  # Perform the reboot
    for _ in range(20):
        try:
            return requests.head(f"http://{wled_ip}/json/", timeout=1)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    time.sleep(5)  # Once it's booted, give it more time to get the json api responding

def set_linear_segment(wled_ip, num_leds):

    print("Setting segment of length ", num_leds)
    segment = {}
    segment["id"] = 0
    segment["start"] = 0
    segment["stop"] = num_leds
    segment["startY"] = 0
    segment["stopY"] = 2
    segment["len"] = num_leds
    segment["col"] = [[255, 0, 255], [0, 0, 0], [0, 0, 0]]
    segment["fx"] = 0
    segment["sel"] = True
    segment["on"] = True

    state = {}
    state["on"] = True
    state["mainseg"] = 0
    state["seg"] = [segment]
    state["ledmap"] = 0

    response = requests.post(
        f"http://{wled_ip}/json/state", data=json.dumps(state), timeout=5
    )
    print("Setting segment response ", response.text)
    return response

def set_2d_segment(wled_ip, width, height, ledmap_id):
    segment = {}
    segment["id"] = 0
    segment["start"] = 0
    segment["stop"] = width
    segment["startY"] = 0
    segment["stopY"] = height
    segment["len"] = width * height
    segment["col"] = [[255, 0, 255], [0, 0, 0], [0, 0, 0]]
    segment["fx"] = 0
    segment["sel"] = True
    segment["on"] = True

    state = {}
    state["seg"] = [segment]
    state["ledmap"] = ledmap_id


    response = requests.post(
        f"http://{wled_ip}/json/state", data=json.dumps(state), timeout=5
    )
    print("Setting segment response ", response.text)
    return response

def apply_ledmap(wled_ip, ledmap_name):
    response = upload_ledmap(wled_ip, ledmap_name)
    if response.status_code != 200:
        return
    reboot_wled(wled_ip)
    ledmap_id = set_current_ledmap_to_name(wled_ip, ledmap_name)

    state = get_full_state(wled_ip)
    if state["ledmap"] != ledmap_id:
        print("LEDmap not set properly")
    return ledmap_id
