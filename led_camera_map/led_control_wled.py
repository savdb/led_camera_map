import json
from requests import get, post



def get_full_info(wled_ip):
    info_response = get(f"http://{wled_ip}/json/info")
    return json.loads(info_response.text)


def get_full_state(wled_ip):
    state_response = get(f"http://{wled_ip}/json/state")
    return json.loads(state_response.text)


def get_led_count(wled_ip):
    info = get_full_info(wled_ip)
    return info["leds"]["count"]


def set_ledmap(wled_ip, ledmap_id):
    state = {}
    state["ledmap"] = ledmap_id
    return post(f"http://{wled_ip}/json/state", data=json.dumps(state))
