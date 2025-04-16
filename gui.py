import sys
from datetime import datetime
from time import time
import csv
import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QPushButton, QLabel,
    QTextBrowser, QInputDialog, QMessageBox, QLineEdit, QCheckBox, QFormLayout,
    QHBoxLayout, QFrame, QRadioButton, QButtonGroup, QGridLayout, QDoubleSpinBox, QTabBar
)
from PyQt6.QtGui import QIcon, QIntValidator
from adbutils import adb

from bot import Bot
from client import Client
from detection import scan


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.connected_emulators = []

        main_layout = QVBoxLayout(self)

        # Tab Widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabBar().setMovable(True)
        self.tab_widget.tabBar().tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tab_widget)

        # Info Tab
        self.info_tab = InfoTab()
        self.tab_widget.addTab(self.info_tab, 'Info')
        # Makes info tab unable to be closed
        info_tab_index = self.tab_widget.indexOf(self.info_tab)
        close_button = self.tab_widget.tabBar().tabButton(info_tab_index, QTabBar.ButtonPosition.RightSide)
        if close_button:
            close_button.resize(0, 0)

        self.tab_widget.setGeometry(5, 5, 300, 490)

        # Add emulator button
        add_emulator_button = QPushButton('Add Emulator Instance', self)
        add_emulator_button.clicked.connect(self.add_emulator_button_event)
        main_layout.addWidget(add_emulator_button)

        # Window Properties
        self.resize(316, 515)
        self.setWindowTitle('e7 Refresh Bot')
        icon_path = 'images\\covenant_bookmark.ico'
        self.setWindowIcon(QIcon(icon_path))

        self.setLayout(main_layout)

    def add_emulator_button_event(self):
        # Get the list of connected emulators
        emulators = adb.device_list()
        emulator_list = [emulator.serial for emulator in emulators if emulator.serial not in self.connected_emulators]
        if not emulator_list:
            # If no emulators are running
            QMessageBox.warning(self, 'Failed to Connect', 'No new running emulators')

        else:
            # Prompt to choose from the list of connected emulators
            emulator, ok = QInputDialog.getItem(self, 'Add Emulator', 'Choose an emulator', emulator_list, 0, False)

            if ok:
                # Create client instance
                client = Client(emulator)
                # Create a new tab
                new_tab = EmulatorTab(client, self)
                # Insert the new tab
                self.tab_widget.insertTab(0, new_tab, f'{emulator}')
                # Focus on the new tab
                self.tab_widget.setCurrentIndex(0)
                # Add device to currently connected devices
                self.connected_emulators.append(emulator)

    def close_tab(self, index):
        tab = self.tab_widget.widget(index)
        if tab.worker_thread and tab.worker_thread.isRunning():
            tab.worker_thread.terminate()
        self.connected_emulators.remove(tab.client.serial)
        self.tab_widget.removeTab(index)

    def closeEvent(self, event):
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if isinstance(tab, EmulatorTab) and tab.worker_thread:
                tab.worker_thread.terminate()
        event.accept()


class InfoTab(QWidget):
    def __init__(self):
        super().__init__()
        info_tab_layout = QVBoxLayout(self)

        # Text Display
        info_layout = QVBoxLayout()
        self.info_text_field = QTextBrowser(self)
        self.info_text_field.setPlainText(
            "Emulator Setup:\n\n"
            "| Resolution: 960x540(dpi 160)\n"
            "| Settings>Others>ADB Debugging=LOCAL\n"
            "| Preferably enable 'Fixed Window Size'\n\n"

            "If you notice the bot missing currencies due to lag, increase the delay (0.3 is default)")
        info_layout.addWidget(self.info_text_field)

        # Delay Setting
        global_option_layout = QGridLayout()
        self.delayInputLabel = QLabel('Delay (secs)')
        self.delay_input = QDoubleSpinBox(self)
        self.delay_input.setDecimals(1)
        self.delay_input.setSingleStep(0.1)
        self.delay_input.setMaximum(2.0)
        self.delay_input.setValue(0.3)
        self.delay_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        global_option_layout.addWidget(self.delayInputLabel, 0, 0)
        global_option_layout.addWidget(self.delay_input, 0, 1)
        info_layout.addLayout(global_option_layout)

        # Image Link
        github_icon = QLabel(self)
        github_icon.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        github_icon.setText(
            '<a href="https://github.com/romanbrancato/e7-refresh-bot">Github</a>')
        github_icon.setOpenExternalLinks(True)
        info_layout.addWidget(github_icon)

        info_tab_layout.addLayout(info_layout)


class EmulatorTab(QWidget):
    def __init__(self, client, window):
        super().__init__()
        self.client = client
        self.window = window

        self.bot = None
        self.worker_thread = None
        self.refreshing = False
        self.last_toggle_time = None

        emulator_tab_layout = QVBoxLayout(self)
        int_validator = QIntValidator(self)

        # Input for Gold and Skystones
        gold_ss_layout = QFormLayout()
        gold_ss_layout.setSpacing(20)
        gold_ss_layout.setVerticalSpacing(5)
        gold_ss_layout.setContentsMargins(45, 0, 45, 0)

        self.goldInputLabel = QLabel('Gold')
        self.goldInput = QLineEdit(self)
        self.goldInput.setValidator(int_validator)
        self.goldInput.setAlignment(Qt.AlignmentFlag.AlignRight)
        gold_ss_layout.addRow(self.goldInputLabel, self.goldInput)

        self.ssInputLabel = QLabel('Skystones')
        self.ssInput = QLineEdit(self)
        self.ssInput.setValidator(int_validator)
        self.ssInput.setAlignment(Qt.AlignmentFlag.AlignRight)
        gold_ss_layout.addRow(self.ssInputLabel, self.ssInput)

        emulator_tab_layout.addLayout(gold_ss_layout)

        # Scan Button
        scan_button_layout = QHBoxLayout()
        scan_button_layout.setContentsMargins(150, 0, 45, 0)
        self.scan_button = QPushButton('Scan', self)
        self.scan_button.clicked.connect(self.scan_currencies)
        scan_button_layout.addWidget(self.scan_button)
        emulator_tab_layout.addLayout(scan_button_layout)

        # Divider
        divider = QFrame(self)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        emulator_tab_layout.addWidget(divider)

        # Option Menu
        option_layout = QGridLayout()
        option_layout.setContentsMargins(45, 0, 45, 0)

        # Check Box
        self.gear_checkbox = QCheckBox('Stop on Red 85 Gear', self)

        # Radio Buttons
        self.radio_button_group = QButtonGroup(self)
        self.bmButton = QRadioButton('Bookmarks')
        self.bmButton.clicked.connect(self.change_option)
        self.bmButton.setChecked(True)
        self.radio_button_group.addButton(self.bmButton, 0)

        self.mmButton = QRadioButton('Mystic Medals')
        self.mmButton.clicked.connect(self.change_option)
        self.radio_button_group.addButton(self.mmButton, 1)

        self.ssButton = QRadioButton('Skystones')
        self.ssButton.clicked.connect(self.change_option)
        self.radio_button_group.addButton(self.ssButton, 2)

        # Radio Button Inputs
        self.bmTargetInput = QLineEdit(self)
        self.bmTargetInput.setValidator(int_validator)
        self.bmTargetInput.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bmTargetInput.setPlaceholderText('Target')

        self.mmTargetInput = QLineEdit(self)
        self.mmTargetInput.setValidator(int_validator)
        self.mmTargetInput.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.mmTargetInput.setPlaceholderText('Target')

        self.ssLimitInput = QLineEdit(self)
        self.ssLimitInput.setValidator(int_validator)
        self.ssLimitInput.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.ssLimitInput.setPlaceholderText('Limit')

        option_layout.addWidget(self.gear_checkbox, 1, 0, 1, 2)
        option_layout.addWidget(self.bmButton, 2, 0)
        option_layout.addWidget(self.bmTargetInput, 2, 1)
        option_layout.addWidget(self.mmButton, 3, 0)
        option_layout.addWidget(self.mmTargetInput, 3, 1)
        option_layout.addWidget(self.ssButton, 4, 0)
        option_layout.addWidget(self.ssLimitInput, 4, 1)
        emulator_tab_layout.addLayout(option_layout)

        # Text Display
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(45, 0, 45, 0)
        self.log_text_field = QTextBrowser(self)
        log_layout.addWidget(self.log_text_field)
        emulator_tab_layout.addLayout(log_layout)

        # Buttons
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.setContentsMargins(45, 0, 45, 0)
        self.refresh_button = QPushButton('Refresh', self)
        self.refresh_button.clicked.connect(self.toggle_bot)
        bottom_buttons_layout.addWidget(self.refresh_button)
        emulator_tab_layout.addLayout(bottom_buttons_layout)

        self.setLayout(emulator_tab_layout)

        # Set initial state for radio buttons
        self.change_option()

        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_log)
        self.log_timer.setInterval(100)

        # Connect to the InfoTab's delay signal for dynamic updates
        self.window.info_tab.delay_input.valueChanged.connect(
            self.handle_delay_update
        )

    def handle_delay_update(self, delay):
        if self.bot:
            self.bot.delay = delay

    def scan_currencies(self):
        currencies = scan(self.client.capture_screen())
        if currencies:
            self.goldInput.setText(currencies[0])
            self.ssInput.setText(currencies[1])
        else:
            self.log_text_field.append("Scan failed to locate currencies")

    def change_option(self):
        button_id = self.radio_button_group.checkedId()
        self.bmTargetInput.setEnabled(button_id == 0)
        self.mmTargetInput.setEnabled(button_id == 1)
        self.ssLimitInput.setEnabled(button_id == 2)

    def toggle_bot(self):
        if not self.refreshing:
            self.start_refreshing()
        else:
            self.stop_refreshing()

        self.refreshing = not self.refreshing
        # Disable all inputs when refreshing
        for btn in self.radio_button_group.buttons():
            btn.setEnabled(not self.refreshing)
        self.bmTargetInput.setEnabled(not self.refreshing and self.bmButton.isChecked())
        self.mmTargetInput.setEnabled(not self.refreshing and self.mmButton.isChecked())
        self.ssLimitInput.setEnabled(not self.refreshing and self.ssButton.isChecked())
        self.scan_button.setEnabled(not self.refreshing)
        self.gear_checkbox.setEnabled(not self.refreshing)

    def start_refreshing(self):
        # Get values from input fields
        stop_condition = self.radio_button_group.checkedId()
        currency_map = {0: "bm", 1: "mm", 2: "ss"}
        input_map = {0: self.bmTargetInput, 1: self.mmTargetInput, 2: self.ssLimitInput}

        currency = currency_map[stop_condition]
        amount = input_map[stop_condition].text()

        config = {
            "delay": self.window.info_tab.delay_input.value(),
            "gold": int(self.goldInput.text() or 0),
            "ss": int(self.ssInput.text() or 0),
            "stop_condition": {"currency": currency, "amount": int(amount or 0), "red_gear": self.gear_checkbox.isChecked()},
        }

        self.bot = Bot(self.client, config)

        self.worker_thread = worker(self.bot)
        self.worker_thread.emitFinished.connect(self.toggle_bot)

        self.worker_thread.start()
        self.last_toggle_time = time()
        self.log_timer.start()
        self.refresh_button.setText('Stop')

    def stop_refreshing(self):
        self.worker_thread.terminate()
        self.log_timer.stop()

        # Calculate stats
        bm_obtained = self.bot.currencies["bm"]["count"]
        mm_obtained = self.bot.currencies["mm"]["count"]
        refreshes = self.bot.refreshes

        # Calculate time spent
        time_spent_seconds = time() - self.last_toggle_time
        hours, remainder = divmod(int(time_spent_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_spent = f'{hours:02}:{minutes:02}:{seconds:02}'

        # Display stats in log
        if self.worker_thread.exception:
            self.log_text_field.append(f'Stopped')
            self.log_text_field.append(f'| Reason: {self.worker_thread.exception}')
        else:
            self.log_text_field.append(f'Finished')

        # Log stats to CSV file

        # Check if file exists to determine need to write headers
        file_exists = os.path.isfile('results.csv')

        current_date = datetime.now().strftime("%Y-%m-%d")

        with open('results.csv', 'a', newline='') as csvfile:
            fieldnames = ['Date', 'Refreshes', 'Bookmarks', 'Mystic Medals', 'Time Spent']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write headers if file is new
            if not file_exists:
                writer.writeheader()

            # Write data row
            writer.writerow({
                'Date': current_date,
                'Refreshes': refreshes,
                'Bookmarks': bm_obtained,
                'Mystic Medals': mm_obtained,
                'Time Spent': time_spent,
            })

        self.refresh_button.setText('Refresh')

    def update_log(self):
        # Update input fields
        self.goldInput.setText(str(self.bot.gold))
        self.ssInput.setText(str(self.bot.ss))

        # Clear previous log content
        self.log_text_field.clear()

        # Calculate runtime duration
        elapsed_seconds = time() - self.last_toggle_time
        hours, remainder = divmod(int(elapsed_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        runtime_str = f"{hours:02}:{minutes:02}:{seconds:02}"

        # Get stop condition parameters
        stop_currency = self.bot.stop_condition["currency"]
        stop_amount = self.bot.stop_condition["amount"]

        # Format currency displays
        bm_count = self.bot.currencies["bm"]["count"]
        mm_count = self.bot.currencies["mm"]["count"]

        bm_display = (f"{bm_count}/{stop_amount}"
                      if stop_currency == "bm" and stop_amount != 0
                      else f"{bm_count}")
        mm_display = (f"{mm_count}/{stop_amount}"
                      if stop_currency == "mm" and stop_amount != 0
                      else f"{mm_count}")

        # Build log content
        log_lines = [
            f"Refreshing [{runtime_str}]",
            f"| Refreshes: {self.bot.refreshes}",
            f"| Bookmarks: {bm_display}",
            f"| Mystic Medals: {mm_display}"
        ]

        # Update log display
        self.log_text_field.setPlainText("\n".join(log_lines))


class worker(QThread):
    emitFinished = pyqtSignal()

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.exception = None

    def run(self):
        try:
            self.bot.handle_refresh()
        except Exception as e:
            self.exception = e
        finally:
            self.emitFinished.emit()


def init():
    app = QApplication(sys.argv)
    app.setStyle('windowsvista')
    window = Window()
    window.show()
    sys.exit(app.exec())
