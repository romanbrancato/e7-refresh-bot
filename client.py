from adbutils import adb
from numpy import asarray


class Client:
    def __init__(self, serial):
        self.serial = serial
        self.device = adb.device(serial=self.serial)

    def capture_screen(self):
        return asarray(self.device.screenshot())

    def click(self, point):
        self.device.click(point[0], point[1])

    def scroll_down(self):
        self.device.swipe(750, 360, 750, 180, 0.1)

    def disconnect(self):
        adb.disconnect(self.serial)
