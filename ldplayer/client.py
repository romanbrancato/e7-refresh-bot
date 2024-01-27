import subprocess


# Have to enable open local connection for adb debugging in settings to use shell commands

def run_command(command):
    adb_args = [r"\LDPlayer\LDPlayer9\dnconsole.exe"] + command
    process = subprocess.Popen(adb_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        return stdout
    else:
        print(f"Error running adb command. Exit code: {process.returncode}\nStderr: {stderr}")


class Client:
    def __init__(self, emulator_index):
        self.emulator_index = emulator_index

    def capture_screen(self):
        screenshot = ["adb", "--index", self.emulator_index, "--command",
                      "shell screencap -p /mnt/shared/Pictures/ss" + self.emulator_index + ".png"]
        run_command(screenshot)

    def click(self, point):
        x, y = point
        location = ["adb", "--index", self.emulator_index, "--command", "shell input tap " + str(x) + " " + str(y)]
        run_command(location)

    def scroll_down(self):
        swipe_down = ["adb", "--index", self.emulator_index, "--command", "shell input swipe 480 360 480 180 100"]
        run_command(swipe_down)
