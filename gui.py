import sys
from datetime import datetime
from time import time
import csv
import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QPushButton, QLabel,
    QTextBrowser, QInputDialog, QMessageBox, QLineEdit, QCheckBox,
    QHBoxLayout, QComboBox, QGridLayout, QDoubleSpinBox, QTabBar
)
from PyQt6.QtGui import QIcon, QIntValidator
from adbutils import adb

from bot import Bot
from client import Client


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

            "If you notice the bot missing currencies, try increasing the delay (0.3 is default)")
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

        # Option Menu
        option_layout = QGridLayout()
        option_layout.setContentsMargins(45, 0, 45, 0)

        # Stop Condition Dropdown
        self.stop_label = QLabel('Choose Stop Condition', self)
        self.stop_dropdown = QComboBox(self)
        self.stop_dropdown.addItem('Bookmarks', 'bm')
        self.stop_dropdown.addItem('Mystic Medals', 'mm')
        self.stop_dropdown.addItem('Skystones', 'ss')
        self.stop_dropdown.addItem('Gold', 'gold')
        self.stop_dropdown.currentIndexChanged.connect(self.change_option)

        self.amountInput = QLineEdit(self)
        self.amountInput.setValidator(int_validator)
        self.amountInput.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Current skystones/gold, only shown for the limit options
        self.currentLabel = QLabel('Current', self)
        self.currentInput = QLineEdit(self)
        self.currentInput.setValidator(int_validator)
        self.currentInput.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Check Box
        self.gear_checkbox = QCheckBox('Stop on Red 85 Gear', self)

        # Keep the space reserved when hidden so the log box doesn't resize
        for widget in (self.currentLabel, self.currentInput):
            size_policy = widget.sizePolicy()
            size_policy.setRetainSizeWhenHidden(True)
            widget.setSizePolicy(size_policy)

        option_layout.addWidget(self.stop_label, 0, 0, 1, 2)
        option_layout.addWidget(self.stop_dropdown, 1, 0)
        option_layout.addWidget(self.amountInput, 1, 1)
        option_layout.addWidget(self.currentLabel, 2, 0)
        option_layout.addWidget(self.currentInput, 2, 1)
        option_layout.addWidget(self.gear_checkbox, 3, 0, 1, 2)
        emulator_tab_layout.addLayout(option_layout)

        # Text Display
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(45, 0, 45, 0)
        self.log_text_field = QTextBrowser(self)
        log_layout.addWidget(self.log_text_field)

        # Current bot action
        self.status_field = QLineEdit(self)
        self.status_field.setReadOnly(True)
        self.status_field.setText('Idle')
        log_layout.addWidget(self.status_field)
        emulator_tab_layout.addLayout(log_layout)

        # Buttons
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.setContentsMargins(45, 0, 45, 0)
        self.refresh_button = QPushButton('Refresh', self)
        self.refresh_button.clicked.connect(self.toggle_bot)
        bottom_buttons_layout.addWidget(self.refresh_button)
        emulator_tab_layout.addLayout(bottom_buttons_layout)

        self.setLayout(emulator_tab_layout)

        # Set initial state for option inputs
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

    def change_option(self):
        is_limit = self.stop_dropdown.currentData() in ('ss', 'gold')
        self.amountInput.setPlaceholderText('Limit' if is_limit else 'Target')
        self.currentLabel.setVisible(is_limit)
        self.currentInput.setVisible(is_limit)
        self.currentInput.setPlaceholderText(self.stop_dropdown.currentText())
        self.currentInput.clear()

    def toggle_bot(self):
        if not self.refreshing:
            if not self.start_refreshing():
                return
        else:
            self.stop_refreshing()

        self.refreshing = not self.refreshing
        # Disable all inputs when refreshing
        self.stop_dropdown.setEnabled(not self.refreshing)
        self.amountInput.setEnabled(not self.refreshing)
        self.currentInput.setEnabled(not self.refreshing)
        self.gear_checkbox.setEnabled(not self.refreshing)

    def start_refreshing(self):
        # Get values from input fields
        currency = self.stop_dropdown.currentData()
        amount = int(self.amountInput.text() or 0)

        current = None
        if currency in ('ss', 'gold'):
            if not self.currentInput.text():
                self.log_text_field.append(f'Enter your current {self.stop_dropdown.currentText().lower()}')
                return False
            current = int(self.currentInput.text())

        config = {
            "delay": self.window.info_tab.delay_input.value(),
            "ss": current if currency == 'ss' else None,
            "gold": current if currency == 'gold' else None,
            "stop_condition": {"currency": currency, "amount": amount, "red_gear": self.gear_checkbox.isChecked()},
        }

        self.bot = Bot(self.client, config)

        self.worker_thread = worker(self.bot)
        self.worker_thread.emitFinished.connect(self.toggle_bot)

        self.worker_thread.start()
        self.last_toggle_time = time()
        self.log_timer.start()
        self.refresh_button.setText('Stop')
        return True

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

        self.status_field.setText('Idle')
        self.refresh_button.setText('Refresh')

    def update_log(self):
        # Update current skystones/gold field
        if self.bot.ss is not None:
            self.currentInput.setText(str(self.bot.ss))
        elif self.bot.gold is not None:
            self.currentInput.setText(str(self.bot.gold))

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
        self.status_field.setText(self.bot.status)


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
