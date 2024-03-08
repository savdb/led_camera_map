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
    return info["leds"]["count"]


def set_current_ledmap(wled_ip, ledmap_name):
    info = get_full_info(wled_ip)
    ledmap_id = 0

    for ledmap in info["maps"]:
        if "n" in ledmap and ledmap["n"] in (ledmap_name, ledmap_name + ".json"):
            ledmap_id = ledmap["id"]

    print("Setting LEDMap to id", str(ledmap_id))
    info = {}
    info["ledmap"] = ledmap_id
    response = requests.post(
        f"http://{wled_ip}/json/state", data=json.dumps(info), timeout=5
    )
    print("Set LEDmap response ", response.text)
    return ledmap_id


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


def apply_ledmap(wled_ip, ledmap_name):
    response = upload_ledmap(wled_ip, ledmap_name)
    if response.status_code != 200:
        return
    reboot_wled(wled_ip)
    ledmap_id = set_current_ledmap(wled_ip, ledmap_name)

    state = get_full_state(wled_ip)
    if state["ledmap"] != ledmap_id:
        print("LEDmap not set properly")
