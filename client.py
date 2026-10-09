import struct
from threading import Thread

from adbutils import adb
from numpy import frombuffer, uint8


class Client:
    def __init__(self, serial):
        self.serial = serial
        self.device = adb.device(serial=self.serial)

    def capture_screen(self):
        # Raw screencap skips PNG encoding/decoding, roughly twice as fast
        data = self.device.shell(['screencap'], encoding=None)
        width, height = struct.unpack('<II', data[:8])
        # Header is 12 or 16 bytes depending on Android version, pixels are RGBA
        pixels = data[len(data) - width * height * 4:]
        return frombuffer(pixels, uint8).reshape(height, width, 4)[:, :, :3].copy()

    def click(self, point):
        self.device.click(point[0], point[1])

    def press(self, point, duration=1.5):
        # Hold down on a point in the background, a swipe that doesn't move is a long press
        self.press_thread = Thread(target=self.device.swipe, args=(point[0], point[1], point[0], point[1], duration))
        self.press_thread.start()

    def release(self):
        # adb can't lift early, so wait for the hold to finish
        self.press_thread.join()

    def scroll_down(self):
        self.device.swipe(750, 360, 750, 180, 0.1)
