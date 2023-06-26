import subprocess


# Have to enable open local connection for adb debugging in settings to use shell commands

class Client:
    def __init__(self, index):
        self.index = index

    def run_command(self, command):
        """Run a command with ADB and return the output as a string"""
        adb_args = ["\\LDPlayer\\LDPlayer9\\dnconsole.exe"] + command

        process = subprocess.Popen(adb_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            output, error = process.communicate(timeout=3)
            output = output.decode().strip()  # Convert bytes to string and remove leading/trailing whitespace
            return output
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            print("Command timed out")
            return None

    def capture_screen(self):
        screenshot = ["adb", "--index", self.index, "--command", "shell screencap -p /mnt/shared/Pictures/ss" + self.index + ".png"]
        self.run_command(screenshot)

    def click_on_location(self, point):
        x, y = point
        location = ["adb", "--index", self.index, "--command", "shell input tap " + str(x) + " " + str(y)]
        self.run_command(location)

    def scroll_down(self):
        swipe_down = ["adb", "--index", self.index, "--command", "shell input swipe 480 360 480 180 100"]
        self.run_command(swipe_down)

    def setup(self):
        setup = ["modify", "--index", self.index, "--resolution", "960,540,160", "--lockwindow", "1"]
        reboot = ["reboot", "--index", self.index]
        self.run_command(setup)
        self.run_command(reboot)
