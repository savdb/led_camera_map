from __future__ import annotations
from typing import Callable

import asyncio
import multiprocessing as mp
from multiprocessing.synchronize import Event
import os
import queue
import cv2 as cv


def do_nothing(_):
    pass


def open_camera(camera_id):
    vc = cv.VideoCapture(camera_id)
    if not vc.isOpened():  # try to get the first frame
        print("Can't open camera")
        vc.release()
        cv.destroyAllWindows()
        exit()
    return vc


# contrast should be different values?
def tweak_contrast(gray_image, contrast):
    return cv.addWeighted(gray_image, contrast, gray_image, 0, 0)


def overlay_text(image):
    image = cv.cvtColor(image, cv.COLOR_GRAY2RGB)
    return cv.putText(
        image,
        "Press Esc to exit calibration",
        (5, 50),
        cv.FONT_HERSHEY_SIMPLEX,
        fontScale=1,
        color=255,
        thickness=2,
    )


def create_threshold(grey_image, threshold):
    margin = 1 + threshold
    # threshold = int( maxVal * margin)
    threshold_value = margin

    _, threshold_image = cv.threshold(
        grey_image, threshold_value, 255, cv.THRESH_BINARY
    )
    return threshold_image


def locate_led_in_image(threshold_image):
    minimum_dimension = 3

    edged_image = threshold_image.copy()
    contours, _ = cv.findContours(edged_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        biggest_contour = max(contours, key=len)
        x, y, w, h = cv.boundingRect(biggest_contour)

        if w > minimum_dimension and h > minimum_dimension:
            contour_image = cv.cvtColor(threshold_image, cv.COLOR_GRAY2RGB)
            cv.rectangle(contour_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cx = int(x + (w / 2))
            cy = int(y + (h / 2))
            return (cx, cy), contour_image

    return (-1, -1), edged_image  # Nothing found in this image


def get_led_position(frame, contrast, threshold):
    gray_image = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    contrast_image = tweak_contrast(gray_image, contrast)

    threshold_image = create_threshold(contrast_image, threshold)
    location, contour_image = locate_led_in_image(threshold_image)

    return location, contour_image, contrast_image


# CV is old and doesn't understand asyncio. This is likely where you're locking up.
# So we spawn another python interpreter and pipe the results back.
class LaunchCalibrationWindowProc(mp.Process):
    def __init__(self, camera_id: int) -> None:
        super().__init__(name="camera-calibration-proc")
        self._camera_id = camera_id
        self.output: mp.Queue[tuple[int, int]]= mp.Queue()
        self.stop_event = mp.Event()
        self.contrast: int | None = None
        self.threshold: int | None = None

    @property
    def result(self) -> tuple[int, int] | tuple[None, None]:
        try:
            # Burn down the whole queue to get the last values.
            while True:
                self.contrast, self.threshold = self.output.get_nowait()
        except queue.Empty:
            return self.contrast, self.threshold

    # Wrap up a queue monitor in a nice, async bow.
    async def get_results(self) -> tuple[int, int] | tuple[None, None]:
        result = None
        while not self.stop_event.is_set():
            try:
                # Inner while loop to burn down the queue again.
                while True:
                    result = self.output.get_nowait()
            except queue.Empty:
                asyncio.sleep(0.050)
        if result is not None:
            self.contrast, self.threshold = result
        return self.contrast, self.threshold

    def run(self) -> None:
        window_name = "Camera Calibration"
        cv.namedWindow(window_name)
        cv.createTrackbar("Threshold", window_name, 230, 255, do_nothing)
        cv.createTrackbar("Contrast", window_name, 1, 5, do_nothing)

        vc = open_camera(self._camera_id)
        print("Calibration window is opened")

        while True:
            success, frame = vc.read()
            if not success:
                print("Couldn't get frame, exiting")
                break

            contrast = cv.getTrackbarPos("Contrast", window_name)
            threshold = cv.getTrackbarPos("Threshold", window_name)
            # N.B. this queue is unbounded, don't leave the calibration window open overnight!
            self.output.put((contrast, threshold))

            _, contour_image, gray_image = get_led_position(frame, contrast, threshold)
            gray_image = overlay_text(gray_image)
            cv.imshow(window_name, gray_image)
            cv.imshow("Detected LED", contour_image)

            # Wait for escape key
            key = cv.waitKey(20)
            if key == 27:  # exit on ESC
                break

        print("Destroying calibration windows")
        cv.destroyAllWindows()
        vc.release()
        self.stop_event.set()


def launch_calibration_window(camera_id: int) -> tuple[int, int] | tuple[None, None]:
    window_name = "Camera Calibration"
    cv.namedWindow(window_name)
    cv.createTrackbar("Threshold", window_name, 230, 255, do_nothing)
    cv.createTrackbar("Contrast", window_name, 1, 5, do_nothing)

    vc = open_camera(camera_id)
    print("Calibration window is opened")

    contrast: int | None = None
    threshold: int | None = None

    while True:
        success, frame = vc.read()
        if not success:
            print("Couldn't get frame, exiting")
            break

        contrast = cv.getTrackbarPos("Contrast", window_name)
        threshold = cv.getTrackbarPos("Threshold", window_name)

        _, contour_image, gray_image = get_led_position(frame, contrast, threshold)
        gray_image = overlay_text(gray_image)
        cv.imshow(window_name, gray_image)
        cv.imshow("Detected LED", contour_image)

        # Wait for escape key
        key = cv.waitKey(20)
        if key == 27:  # exit on ESC
            break

    print("Destroying calibration windows")
    cv.destroyAllWindows()
    vc.release()
    return contrast, threshold


def draw_all_led_positions(locations, image):
    print("Drawing locations on image")

    # Put into grayscale, then back into color
    image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    image = cv.cvtColor(image, cv.COLOR_GRAY2RGB)

    for led_index, coordinates in enumerate(locations):
        image = cv.circle(image, coordinates, radius=5, color=(255, 0, 0), thickness=2)
        image = cv.putText(
            image,
            str(led_index),
            coordinates,
            cv.FONT_HERSHEY_SIMPLEX,
            fontScale=1,
            color=255,
            thickness=2,
        )
    return image


def get_frame(vc):
    success, frame = vc.read()
    if not success:
        print("Couldn't get frame, exiting")
        return None
    return frame


def generate_output_image(locations, name):
    print("Creating output image")
    vc = cv.VideoCapture(0)
    if not vc.isOpened():  # try to get the first frame
        print("Can't open camera")
        vc.release()
        exit()
    success, frame = vc.read()
    if not success:
        print("Couldn't get frame, exiting")
        return
    img = draw_all_led_positions(locations, frame)
    status = cv.imwrite(name + ".png", img)
    print("Image of LED locations saved: ", status)
    if status:
        os.system("start " + name + ".png")
