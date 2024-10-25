from adbutils import adb, AdbTimeout, AdbError
from numpy import asarray


# Must enable open local/remote connection for adb debugging in emulator settings

# The following functions are tailored for ldplayer as adb.device_list() always returns ld devices serials as
# emulator-####. However, connecting using that is much slower than parsing the port then connecting directly to the
# address 1 port above it. If this were to be changed to be used with other emulators: adb.connect(device.serial)
def connect_all():
    connected_devices = []
    for device in adb.device_list():
        try:
            port = int(device.serial[-4:]) + 1
            adb.connect(f"127.0.0.1:{port}", timeout=0.1)
            connected_devices.append(f"127.0.0.1:{port}")
        except AdbTimeout as e:
            print(e)
    return connected_devices


def disconnect_all():
    disconnected_devices = []
    for device in adb.device_list():
        try:
            port = int(device.serial[-4:]) + 1
            adb.disconnect(f"127.0.0.1:{port}")
            disconnected_devices.append(f"127.0.0.1:{port}")
        except AdbError as e:
            print(e)
    return disconnected_devices


class Client:
    def __init__(self, address):
        self.address = address
        self.device = adb.device(serial=self.address)

    def capture_screen(self):
        return asarray(self.device.screenshot())

    def click(self, point):
        self.device.click(point[0], point[1])

    def scroll_down(self):
        self.device.swipe(750, 360, 750, 180, 0.1)

    def disconnect(self):
        adb.disconnect(self.address)
