#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import concurrent.futures
from contextlib import suppress
from led_camera_map import camera, format_map, led_control_artnet, led_control_wled

WLED_IP = "wled.local"
LED_MAP_OUTPUT_NAME = "ledmap2"
CAMERA_ID = 0


def cancel_all_tasks():
    pending = asyncio.all_tasks()
    pending.remove(asyncio.current_task())
    with suppress(asyncio.CancelledError):
        for task in pending:
            task.cancel()


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

def get_user_confirmation(message:str):
    print(message)
    key_pressed = input(str("Type y and press Enter to confirm, any other input will exit: "))
    if not key_pressed.casefold() in ("y", "yes", "ok", "continue"):
        print("Exiting")
        quit() 

async def run_mapping_task(brightness, threshold, num_leds):
    locations = []
    channel = await led_control_artnet.setup_artnet_leds(WLED_IP, num_leds)

    vc = camera.open_camera(CAMERA_ID)

    print(
        "Starting LED location capture with LED brightness "
        + str(brightness)
        + " and threshold "
        + str(threshold)
    )
    for i in range(num_leds):
        await led_control_artnet.light_one_led(channel, num_leds, i, brightness)
        await asyncio.sleep(0)

        frame = camera.get_frame(vc)
        location, _, _ = camera.get_led_position(
            frame, threshold, save_image=True, minimum_dimension=0
        )

        # if not location == (-1, -1):
        # if not location_already_found(locations, location, 3):
        print("Found LED at ", location)
        locations.append(location)

    print("Finishing LED location capture")
    vc.release()

    return locations


async def main():
    print("Getting number of LEDs from WLED")
    print("If this is a different number than you expected, go to 2D configuration")
    print("and make sure your width is the number of LEDs and the height is 2.")
    num_leds = led_control_wled.get_led_count(WLED_IP)
    print("WLED reports", num_leds, "LEDs")  # ArtNet requires 512 or less per universe
    get_user_confirmation("Is that the number of LEDs you expected?")

    print("Setting WLED's /ledmap0.json to a basic linear map")
    format_map.generate_basic_ledmap(num_leds) # creates out/ledmap0.json
    led_control_wled.apply_ledmap(WLED_IP, "ledmap0")

    print("Creating basic linear segment")
    led_control_wled.set_linear_segment(WLED_IP, num_leds)

    calibration_proc = camera.LaunchCalibrationWindowProc(CAMERA_ID)
    calibration_proc.start()
    brightness_queue = calibration_proc.output

    led_blink_task = None
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        led_blink_task = await loop.run_in_executor(
            pool,
            led_control_artnet.calibration_blink,
            WLED_IP,
            num_leds,
            brightness_queue,
        )
    print("==== PRESS ESC TO FINISH CALIBRATION ===")
    await led_blink_task
    brightness, threshold = await calibration_proc.get_results()
    assert brightness is not None, "Ensure the proc is done, and you have values."
    assert threshold is not None, "Ensure that the proc is done, and you have values."
    calibration_proc.join()

    print("Stopping calibration LED blink")
    cancel_all_tasks()  # Let's cancel all running tasks before continuing

    locations = await run_mapping_task(brightness, threshold, num_leds)
    print("Found positions of ", str(len(locations)), " LEDs: ")
    print(locations)

    linear_list, width, height = format_map.flatten_2d_map(locations)
    camera.generate_output_image(CAMERA_ID, locations, LED_MAP_OUTPUT_NAME)
    ledmap_json = format_map.save_wled_json(
        LED_MAP_OUTPUT_NAME, linear_list, width, height
    )
    format_map.visualize_ledmap(ledmap_json)

    get_user_confirmation("Upload this ledmap to WLED?")
    print("Proceeding to upload ledmap to WLED")
    ledmap_id = led_control_wled.apply_ledmap(WLED_IP, LED_MAP_OUTPUT_NAME)
    led_control_wled.set_2d_segment(WLED_IP, width, height, ledmap_id)

    print("All done")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
