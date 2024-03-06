#!/usr/bin/env python3

import asyncio
from contextlib import suppress
from concurrent.futures.process import ProcessPoolExecutor
import json
from wled_camera_map import led_control, camera, format_map

WLED_IP = "1.1.1.1"
NUM_LEDS = 10  # TODO: Get this value from wLED API
LED_MAP_OUTPUT_NAME = "cvMap"
CAMERA_ID = 0

def cancel_all_tasks():
    pending = asyncio.all_tasks()
    pending.remove(asyncio.current_task())
    with suppress(asyncio.CancelledError):
        for task in pending:
            task.cancel()
    # await asyncio.sleep(3) # And also sleep for a bit to let the LEDs settle

def location_already_found(locations, this_location, distance):
    # Check the last location first, since it's most likely to be what's nearby
    for location in reversed(locations):
        if (
            abs(this_location[0] - location[0]) < distance
            and abs(this_location[1] - location[1]) < distance
        ):
            # print ("Found existing location ", location, thisLocation)
            return True
    return False

async def main():
    led_blink_task = asyncio.get_event_loop().create_task(
        led_control.calibration_blink(WLED_IP)
    )
    await asyncio.sleep(0)
    print("Starting Calibration Window")
    contrast, threshold = await asyncio.get_event_loop().run_in_executor(
        None, camera.launch_calibration_window, CAMERA_ID
    )
    print("Stopping calibration LED blink")
    led_blink_task.cancel()
    cancel_all_tasks()  # Let's cancel all running tasks before continuing

    locations = []
    channel = await led_control.setup_leds(WLED_IP)

    vc = camera.open_camera(CAMERA_ID)

    print("Starting LED location capture")
    for i in range(NUM_LEDS):
        await led_control.light_one_led(channel, i)
        await asyncio.sleep(0.5)

        frame = camera.get_frame(vc)
        location, _, _ = camera.get_led_position(frame, contrast, threshold)

        if not location == (-1, -1):
            if not location_already_found(locations, location, 3):
                print("Found LED at ", location)
                locations.append(location)

    print("Finishing LED location capture")
    vc.release()

    print("Found positions of ", str(len(locations)), " LEDs: ")
    positions_2d_list = [list(elem) for elem in locations]  # Convert to list-of-lists
    print(positions_2d_list)

    linear_list, width, height = format_map.convert_2d_map_to_1d(positions_2d_list)
    ledmap_json = format_map.create_wled_json(
        linear_list, width, height, LED_MAP_OUTPUT_NAME
    )
    print("Genered ", LED_MAP_OUTPUT_NAME, ".json")
    # print(ledmap_json)

    with open(LED_MAP_OUTPUT_NAME + ".json", "w", encoding="utf8") as outfile:
        json.dump(ledmap_json, outfile)

    # TODO: Use API to upload ledmap.json to WLED
    # TODO: WLED needs to be rebooted after ledmap files are uploaded?

    camera.generate_output_image(locations, LED_MAP_OUTPUT_NAME)
    print("All done")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_default_executor(ProcessPoolExecutor())
    loop.run_until_complete(main())
