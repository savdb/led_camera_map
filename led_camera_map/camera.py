import os
import cv2 as cv

FRAMES_SAVED_COUNTER = 0

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


def locate_led_in_image(threshold_image, minimum_dimension=3):
    minimum_dimension = 3

    edged_image = threshold_image.copy()
    contours, _ = cv.findContours(edged_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        biggest_contour = max(contours, key=cv.contourArea)
        x, y, w, h = cv.boundingRect(biggest_contour)

        if w >= minimum_dimension and h >= minimum_dimension:
            contour_image = cv.cvtColor(threshold_image, cv.COLOR_GRAY2RGB)
            cv.rectangle(contour_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cx = int(x + (w / 2))
            cy = int(y + (h / 2))
            return (cx, cy), contour_image

    return (-1, -1), edged_image  # Nothing found in this image


def get_led_position(frame, threshold, save_image=False, minimum_dimension=3):
    gray_image = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    threshold_image = create_threshold(gray_image, threshold)
    location, contour_image = locate_led_in_image(threshold_image, minimum_dimension)
    if save_image:
        global FRAMES_SAVED_COUNTER
        cv.imwrite("out/led" +str(FRAMES_SAVED_COUNTER) + ".png", contour_image)
        FRAMES_SAVED_COUNTER += 1

    return location, contour_image, gray_image


def launch_calibration_window(camera_id):
    window_name = "Camera Calibration"
    cv.namedWindow(window_name)
    cv.createTrackbar("Threshold", window_name, 230, 255, do_nothing)
    cv.createTrackbar("LED_Brightness", window_name, 128, 255, do_nothing)

    vc = open_camera(camera_id)
    print("Calibration window is opened")

    while True:
        success, frame = vc.read()
        if not success:
            print("Couldn't get frame, exiting")
            break

        threshold = cv.getTrackbarPos("Threshold", window_name)
        brightness = cv.getTrackbarPos("LED_Brightness", window_name) #TODO: Use this in led_control

        _, contour_image, gray_image = get_led_position(frame, threshold)
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
    return threshold


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
    # frame = cv.resize(frame, dsize=(75,75), interpolation=cv.INTER_CUBIC)
    return frame


def generate_output_image(camera_id, locations, name):
    print("Creating output image")
    vc = cv.VideoCapture(camera_id)
    if not vc.isOpened():  # try to get the first frame
        print("Can't open camera")
        vc.release()
        exit()
    success, frame = vc.read()
    if not success:
        print("Couldn't get frame, exiting")
        return
    img = draw_all_led_positions(locations, frame)
    status = cv.imwrite("out/"+name + ".png", img)
    print("Image of LED locations saved: ", status)
    if status:
        os.system("start out/" + name + ".png")
