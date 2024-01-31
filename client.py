from adbutils import adb, AdbTimeout, AdbError
from numpy import asarray


# Must enable open local/remote connection for adb debugging in emulator settings

# adb_connect_all and adb_disconnect_all assume that all emulator addresses have an ip of 127.0.0.1 and a port
# pattern of (5555 + index * 2) (according to LDPlayer themselves) If this were to be made to work on other emulators
# ensure that the above rule is true
def adb_connect_all():
    connected_devices = []
    device_list = adb.device_list()
    if device_list:
        last_device_port = int(device_list[-1].serial[-4:]) + 1
        for port in range(5555, last_device_port + 2, 2):
            try:
                adb.connect(f"127.0.0.1:{port}", timeout=1)
                connected_devices.append(f"127.0.0.1:{port}")
            except AdbTimeout as e:
                print(e)
    return connected_devices


def adb_disconnect_all():
    disconnected_devices = []
    device_list = adb.device_list()
    if device_list:
        last_device_port = int(device_list[-1].serial[-4:]) + 1
        for port in range(5555, last_device_port + 2, 2):
            try:
                adb.disconnect(f"127.0.0.1:{port}", raise_error=True)
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
