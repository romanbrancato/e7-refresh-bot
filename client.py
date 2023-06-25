import subprocess

# had to enable open local connection for adb debugging in settings to use shell commands

def run_command(command):
    """Run a command with ADB and return the output"""
    adb_args = ["\\LDPlayer\\LDPlayer9\\dnconsole.exe", "adb", "--name", "Epic Seven", "--command", command]

    process = subprocess.Popen(adb_args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        outs, errs = process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        outs, errs = process.communicate()
        print("Command timed out")

    return (errs or outs).decode("utf-8")


def capture_screen():
    screenshot = "shell screencap -p /mnt/shared/Pictures/ss.png"
    run_command(screenshot)


def click_on_location(point: tuple):
    x, y = point
    location = "shell input tap " + str(x) + " " + str(y)
    run_command(location)


def scroll_down():
    swipe_down = "shell input swipe 480 360 480 180 100"
    run_command(swipe_down)
