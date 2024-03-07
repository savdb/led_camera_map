# LED Camera Mapper

This project uses a camera to capture the location of addressable LEDs in 2d, and outputs a ledmap.json that can be used in WLED.

It communicates with a WLED instance via ArtNet to blink the LEDs, then uses OpenCV to detect the coordinates of their location in the camera image.