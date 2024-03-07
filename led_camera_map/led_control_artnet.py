from __future__ import annotations

from typing import NoReturn
import asyncio
from pyartnet import ArtNetNode, Channel

CHANNELS_PER_LED = 3
WLED_TIMEOUT_MS = 2500


def get_channel_width(num_leds: int):
    return (num_leds * CHANNELS_PER_LED) + 1  # Assuming mode "Dimmer + Multi RGB"


async def setup_artnet_leds(ip_address: str, num_leds: int) -> Channel:
    node = ArtNetNode(ip_address, 6454)
    universe = node.add_universe(0)
    return universe.add_channel(start=1, width=get_channel_width(num_leds))


def create_single_pixel_channel(
    num_leds: int, position: int, brightness: int
) -> list[int]:
    array = [0] * get_channel_width(num_leds)
    array[0] = (
        brightness  # First entry in the array is the brightness of the whole array
    )
    start = 1 + position * CHANNELS_PER_LED
    for i in range(start, start + CHANNELS_PER_LED):
        array[i] = 255
    return array


async def light_one_led(channel: Channel, num_leds: int, i: int, brightness: int):
    print("Lighting up LED ", i)
    await channel.set_values(create_single_pixel_channel(num_leds, i, brightness))
    await asyncio.sleep(0.2)


async def flash_leds_in_order(ip_address, num_leds, brightness: int):
    print("entering blink")
    channel = await setup_artnet_leds(ip_address, num_leds)
    print("LEDs are ready")
    for i in range(num_leds):
        print("Lighting up pixel ", i)
        channel.add_fade(create_single_pixel_channel(num_leds, i, brightness), 200)
        await channel
        await asyncio.sleep(1)


async def blink_one_led_continuously(
    channel: Channel, num_leds: int, i: int, brightness_queue
):
    while True:
        current_brightness, _ = brightness_queue.get()
        print("Blinking LED" + str(i) + " at brightness " + str(current_brightness))
        await channel.set_values(
            create_single_pixel_channel(num_leds, i, current_brightness)
        )
        await asyncio.sleep(1)
        all_off_array = [0] * get_channel_width(
            num_leds
        )  # Brightness is 0 and all LEDs are black
        await channel.set_values(all_off_array)
        await asyncio.sleep(1)


async def calibration_blink(
    ip_address: str, num_leds: int, brightness_queue
) -> asyncio.Task[NoReturn]:
    print("Setting up LEDs")
    channel = await setup_artnet_leds(ip_address, num_leds)
    print("LEDs are ready")
    return asyncio.ensure_future(
        blink_one_led_continuously(channel, num_leds, 1, brightness_queue)
    )
