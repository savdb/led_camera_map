from __future__ import annotations

from typing import NoReturn
import asyncio
from pyartnet import ArtNetNode, Channel

NUM_LEDS = 100 # TODO: Get this value from main()
CHANNELS_PER_LED  = 3
CHANNEL_WIDTH = NUM_LEDS * CHANNELS_PER_LED
WLED_TIMEOUT_MS = 2500


async def setup_leds(ip_address: str) -> Channel:
    node = ArtNetNode(ip_address, 6454)
    universe = node.add_universe(0)
    return universe.add_channel(start=1, width=CHANNEL_WIDTH)

def create_single_pixel_channel(position: int) -> list[int]:
    array = [0] * CHANNEL_WIDTH
    start = position * CHANNELS_PER_LED
    for i in range(start, start + CHANNELS_PER_LED):
        array[i] = 255
    return array

async def light_one_led(channel, i):
    print("Lighting up LED ", i)
    await channel.set_values(create_single_pixel_channel(i))
    await asyncio.sleep(0.5)

async def blink_one_led_continuously(channel: Channel, i: int):
    while True:
        print("==== PRESS ESC TO FINISH CALIBRATION ===")
        await channel.set_values(create_single_pixel_channel(i))
        await asyncio.sleep(1)
        all_off_array = [0]*CHANNEL_WIDTH
        await channel.set_values(all_off_array)
        await asyncio.sleep(1)

async def flash_leds_in_order(ip_address,num_leds):
    print("entering blink")
    channel = await setup_leds(ip_address)
    print("LEDs are ready")
    for i in range(num_leds):
        print("Lighting up pixel ", i)
        channel.add_fade(create_single_pixel_channel(i), 200)
        await channel
        await asyncio.sleep(1)

async def calibration_blink(ip_address) -> asyncio.Task[NoReturn]:
    print("Setting up LEDs")
    channel = await setup_leds(ip_address)
    print("LEDs are ready")
    return asyncio.ensure_future(blink_one_led_continuously(channel, 1))
