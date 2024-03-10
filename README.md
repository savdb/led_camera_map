# LED Camera Mapper

This project uses a camera to capture the location of addressable LEDs in 2d, and outputs a ledmap.json that can be used in WLED.

It communicates with a WLED instance via ArtNet to blink the LEDs, then uses OpenCV to detect the coordinates of their location in the camera image.

This program was written to run on a computer with a webcam pointing at the LEDs, on the same network as the WLED instance so it can communicate wirelessly.  I used [the MoonModules fork](https://mm.kno.wled.ge/) of WLED while developing this, due to better 2D support. At time of writing, the version I used is `WLEDMM_0.14.1-b30.36 esp32_4MB_M`.

## Setup steps in WLED MM

1. Set the total number of LEDs you have in Setup > Config > LEDs > Hardare setup > Length
2. Put WLED into 2D mode in Setup > 2D Configuration > 2D Matrix > Panel Dimensions.  Set width equal to about the number of LEDs you have. Set the height to 2.  This gives you a basically linear strip, but in 2d mode, which is required for mapping. If your Total LEDs is more than 512, they won't all fit into one ArtNet universe (current code assumes one ArtNet universe only)
3. Enable ArtNet in Setup > Sync Interfaces > Realtime.  Set the following settings, then save and reboot WLED.
    - Type: Art-Net
    - Multicast: True
    - Start Universe: 0
    - DMX mode: Dimmer + Multi RGB
4. WLED really likes having a few LEDmaps in its system before it displays all the information.  Go to `http://your-wled-instance.local/edit` and create some files named`/ledmap0.json` (this one is always called "Default" in the UI), `/ledmap1.json`, and `/ledmap2.json`.  Those `/` characters at the beginning of the filenames are important, don't leave them out.  You can populate these LEDmap files with any valid ledmap (like the LinearMap example above, something from [a ledmap generator](https://dosipod.github.io/WLED-Ledmap-Generator/), etc).  It's just nice to have those files around so WLED starts showing you the LEDmap options on the UI.  Also, having a file named `/ledmap.json` (no number) seems to mess things up, so don't have one of those.
5. Ensure `ledmap0.json` (called "Default" in the web UI) is configured as a default linear LED map, something like this. Otherwise, the calibration LEDs will flash in the order of your LEDMap and the output of this tool will be incorrect.  Make sure this includes all your LEDs.

    ```json
    {"n":"LinearMapFor20LEDs"
    ,"width":20
    ,"height":1
    ,"map":[
    0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19]}
    ```

## Setup steps on your computer

1. Set your WLED IP address or mDNS address at the top of mapping.py
2. You can rename the `LED_MAP_OUTPUT_NAME` at the top of mapping.py, but the filename needs to be `ledmap1` through `ledmap9`.  `ledmap0` is the default map in WLED. Other filenames don't work in WLED.
3. Install dependencies listed in `pyproject.toml`. You can use [poetry](https://python-poetry.org/) to do this or install them yourself.
4. In python, run `mapping.py`.
5. The Camera calibration screen will open. If openCV is using a different camera than the one you expect, kill the program and choose a different camera id at the top of `mapping.py` until you see the correct one.

## Running the mapping program

1. Position your camera so that it can see as many of your LEDs as possible. LEDs the camera can't see will be skipped in the generated ledmap.
2. While in the calibration screen, one LED will blink. Change the threshold until the LED screen shows all black when the LED is off, and shows a small red box around the LED when the LED is on. Adjust the LED brightness if necessary to get an accurate size around the LED. If you're having trouble isolating just the LED in the camera calibration, try running in a dark room or with a neutral background.  If your camera is auto-adjusting the brightness/contrast in real-time, hopefully you can turn that off. Good luck.

    __Note:__ Probably don't leave the calibration screen running all day, I didn't do a great job of memory/process management in Python so it might cause issues.

3. Once you're happy with the calibration, press the `Esc` key to close the calibration window. The LED mapping will begin automatically as soon as the calibration window is closed.
4. The program will flash each LED (up to the number of LEDs that WLED says you have), in the order of your currently applied LEDmap.  As it flashes each LED, it captures a screenshot of each one to the `out/` directory.
5. Once all the LEDs have flashed, the program will use the x,y coordinates from the images to compute an LED map.  To compress the map, any rows or columns that didn't have an LED in them will be removed.
6. WLED wants the LEDmap to be in the form of a 1D array with the id of each LED in the array position and blank spaces marked as -1, so the program will convert the `(x,y)` coordinates to this format.
7. The program will save your `ledmap2.json` file to `out/` and also create an image with all the LEDs marked so you can compare the output.
8. After creating the ledmap json file, the program will upload the file to WLED, reboot WLED (sometimes required for these files to show up), and then attempt to apply this LEDmap as the current LED map in WLED.

    __Hopefully after all these steps run, your LEDmap will be somewhat close to reality.__

9. After you have your LEDmap, you'll want to take a look at the width and height in the generated LEDmap and set some more WLED settings based on it.
10. In Settings > 2D Configuration > 2D matrix, set the width and height to match your ledmap.
11. Create a segment with a width and height that encompass all your LEDs
