import sys
from datetime import datetime
from time import time
import csv
import os
import urllib.request

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QPushButton, QLabel, QInputDialog, QMessageBox,
    QLineEdit, QCheckBox, QHBoxLayout, QComboBox, QGridLayout, QGroupBox, QTabBar
)
from PyQt6.QtGui import QColor, QIcon, QIntValidator
from adbutils import adb

from bot import Bot
from client import Client

SETUP_NOTES = (
    "Emulator Setup:\n"
    "  Resolution: 960x540 (DPI 160)\n"
    "  Settings > Others > ADB Debugging = LOCAL\n"
    "  Preferably Enable 'Fixed Window Size'"
)

REPO_URL = 'https://github.com/romanbrancato/e7-refresh-bot'
LATEST_VERSION_URL = 'https://raw.githubusercontent.com/romanbrancato/e7-refresh-bot/main/version.txt'

# Status dot colors
GREY, GREEN, AMBER, RED = '#8c8c8c', '#2ea043', '#e0a800', '#d1242f'


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.connected_emulators = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # Tab Widget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabBar().setMovable(True)
        self.tab_widget.tabBar().tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tab_widget)


        # Info Tab
        self.info_tab = InfoTab()
        self.tab_widget.addTab(self.info_tab, 'Info')
        self.info_tab.update_available.connect(self.show_update_on_tab)
        # Makes info tab unable to be closed
        info_tab_index = self.tab_widget.indexOf(self.info_tab)
        close_button = self.tab_widget.tabBar().tabButton(info_tab_index, QTabBar.ButtonPosition.RightSide)
        if close_button:
            close_button.resize(0, 0)

        # Add emulator button
        add_emulator_button = QPushButton('Add Emulator Instance', self)
        add_emulator_button.clicked.connect(self.add_emulator_button_event)
        main_layout.addWidget(add_emulator_button)

        # Window Properties
        self.resize(316, 450)
        self.setWindowTitle('e7 Refresh Bot')
        icon_path = 'images\\covenant_bookmark.ico'
        self.setWindowIcon(QIcon(icon_path))

        self.setLayout(main_layout)

    def show_update_on_tab(self):
        # Mark the info tab so the update is noticed from any tab
        index = self.tab_widget.indexOf(self.info_tab)
        self.tab_widget.setTabText(index, 'Info ●')
        self.tab_widget.tabBar().setTabTextColor(index, QColor(AMBER))

    def add_emulator_button_event(self):
        # Get the list of connected emulators
        emulators = adb.device_list()
        emulator_list = [emulator.serial for emulator in emulators if emulator.serial not in self.connected_emulators]
        if not emulator_list:
            # If no emulators are running
            QMessageBox.warning(self, 'Failed To Connect', f'No New Running Emulators\n\n{SETUP_NOTES}')

        else:
            # Prompt to choose from the list of connected emulators
            emulator, ok = QInputDialog.getItem(self, 'Add Emulator', 'Choose An Emulator', emulator_list, 0, False)

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
        # Don't leave the update check running after the window is gone
        if self.info_tab.update_checker.isRunning():
            self.info_tab.update_checker.terminate()
            self.info_tab.update_checker.wait()
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if isinstance(tab, EmulatorTab) and tab.worker_thread:
                tab.worker_thread.terminate()
        event.accept()


def read_version(text):
    # "1.2" -> (1, 2) so versions compare numerically
    return tuple(int(part) for part in text.strip().split('.'))


class UpdateChecker(QThread):
    # Fetches the latest version number from GitHub, emits it or None if it couldn't be checked
    checked = pyqtSignal(object)

    def run(self):
        try:
            with urllib.request.urlopen(LATEST_VERSION_URL, timeout=10) as response:
                self.checked.emit(response.read().decode().strip())
        except Exception:
            self.checked.emit(None)


class InfoTab(QWidget):
    update_available = pyqtSignal()

    STEPS = ['Set Up The Emulator As Shown Below', 'Open The Secret Shop In Game',
             'Press Add Emulator Instance', 'Pick Your Options And Press Start']
    SETTINGS = [('Resolution', '960 × 540'), ('DPI', '160'), ('ADB Debugging', 'Local'), ('Fixed Window Size', 'Recommended')]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Getting Started, numbered steps
        steps_box = QGroupBox('Getting Started', self)
        steps_layout = QGridLayout(steps_box)
        steps_layout.setVerticalSpacing(6)
        for i, step in enumerate(self.STEPS):
            number = QLabel(f'{i + 1}.', self)
            number.setStyleSheet('QLabel { font-weight: bold; }')
            steps_layout.addWidget(number, i, 0)
            steps_layout.addWidget(QLabel(step, self), i, 1)
        steps_layout.setColumnStretch(1, 1)
        layout.addWidget(steps_box)

        # Emulator Setup, setting and value
        setup_box = QGroupBox('Emulator Setup', self)
        setup_layout = QGridLayout(setup_box)
        setup_layout.setVerticalSpacing(6)
        for i, (name, value) in enumerate(self.SETTINGS):
            setup_layout.addWidget(QLabel(name, self), i, 0)
            value_label = QLabel(f'<b>{value}</b>', self)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            setup_layout.addWidget(value_label, i, 1)
        where = QLabel('ADB Debugging Is Under Settings > Others', self)
        where.setStyleSheet('QLabel { color: #777; }')
        setup_layout.addWidget(where, len(self.SETTINGS), 0, 1, 2)
        layout.addWidget(setup_box)

        # Version, checked against GitHub in the background
        version_box = QGroupBox('Version', self)
        version_layout = QGridLayout(version_box)
        version_layout.setVerticalSpacing(6)
        with open('version.txt') as version_file:
            self.installed_version = version_file.read().strip()
        version_layout.addWidget(QLabel('Installed', self), 0, 0)
        installed = QLabel(f'<b>{self.installed_version}</b>', self)
        installed.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_layout.addWidget(installed, 0, 1)
        self.update_label = QLabel('Checking For Updates...', self)
        self.update_label.setOpenExternalLinks(True)
        version_layout.addWidget(self.update_label, 1, 0, 1, 2)
        layout.addWidget(version_box)
        layout.addStretch(1)

        self.update_checker = UpdateChecker(self)
        self.update_checker.checked.connect(self.show_update_status)
        self.update_checker.start()

    def show_update_status(self, latest):
        if latest is None:
            self.update_label.setText(f'<span style="color:#777">Couldn\'t Check For Updates</span>')
            return
        try:
            newer = read_version(latest) > read_version(self.installed_version)
        except ValueError:
            newer = False
        if newer:
            self.update_label.setText(f'<span style="color:{AMBER}">●</span>&nbsp; <b>Update Available: {latest}</b>'
                                      f' &nbsp;<a href="{REPO_URL}">Download</a>')
            self.update_available.emit()
        else:
            self.update_label.setText(f'<span style="color:{GREEN}">●</span>&nbsp; Up To Date')


class EmulatorTab(QWidget):
    # Stats shown in the session box, (key, label)
    STATS = [('refreshes', 'Refreshes'), ('bm', 'Bookmarks'), ('mm', 'Mystic Medals'),
             ('fs', 'Friendship'), ('gear', 'Gear Sold'), ('epic', 'Epic Bought')]

    def __init__(self, client, window):
        super().__init__()
        self.client = client
        self.window = window

        self.bot = None
        self.worker_thread = None
        self.refreshing = False
        self.last_toggle_time = None
        self.was_paused = False

        emulator_tab_layout = QVBoxLayout(self)
        emulator_tab_layout.setSpacing(8)
        int_validator = QIntValidator(self)

        # Stop When
        stop_box = QGroupBox('Stop When', self)
        stop_layout = QGridLayout(stop_box)

        self.stop_dropdown = QComboBox(self)
        self.stop_dropdown.addItem('Bookmarks', 'bm')
        self.stop_dropdown.addItem('Mystic Medals', 'mm')
        self.stop_dropdown.addItem('Skystones', 'ss')
        self.stop_dropdown.addItem('Gold', 'gold')
        self.stop_dropdown.currentIndexChanged.connect(self.change_option)

        self.amountInput = QLineEdit(self)
        self.amountInput.setValidator(int_validator)
        self.amountInput.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.amountInput.setFixedWidth(80)

        # Current skystones/gold, only shown for the limit options
        self.currentLabel = QLabel(self)
        self.currentInput = QLineEdit(self)
        self.currentInput.setValidator(int_validator)
        self.currentInput.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.currentInput.setFixedWidth(80)

        stop_layout.addWidget(self.stop_dropdown, 0, 0)
        stop_layout.addWidget(QLabel('Reach', self), 0, 1)
        stop_layout.addWidget(self.amountInput, 0, 2)
        stop_layout.addWidget(self.currentLabel, 1, 0, 1, 2)
        stop_layout.addWidget(self.currentInput, 1, 2)
        stop_layout.setColumnStretch(0, 1)
        emulator_tab_layout.addWidget(stop_box)

        # Also Buy
        buy_box = QGroupBox('Also Buy', self)
        buy_layout = QGridLayout(buy_box)

        self.fs_checkbox = QCheckBox('Friendship', self)
        self.sell_gear_checkbox = QCheckBox('Non-Epic Gear', self)
        self.sell_gear_checkbox.setToolTip('Buys and immediately sells non-epic gear')

        # Epic gear action, minimum equipment score and speed
        self.epic_dropdown = QComboBox(self)
        self.epic_dropdown.addItem('Ignore', 'ignore')
        self.epic_dropdown.addItem('Buy', 'buy')
        self.epic_dropdown.addItem('Pause', 'pause')
        self.epic_dropdown.setToolTip('What to do with level 85 epic gear')
        self.epic_dropdown.currentIndexChanged.connect(self.change_epic_option)

        self.minEsLabel = QLabel('ES ≥', self)
        self.minEsInput = QLineEdit(self)
        self.minEsInput.setValidator(int_validator)
        self.minEsInput.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.minEsInput.setPlaceholderText('Any')
        self.minEsInput.setFixedWidth(32)

        # Always buy epics with speed, whatever their ES
        self.speed_checkbox = QCheckBox('Speed', self)
        self.speed_checkbox.setToolTip('Always buy epic gear with speed, whatever its ES')

        epic_row = QHBoxLayout()
        epic_row.setSpacing(4)
        epic_row.addWidget(QLabel('Epic', self))
        epic_row.addWidget(self.epic_dropdown, 1)
        epic_row.addWidget(self.minEsLabel)
        epic_row.addWidget(self.minEsInput)
        epic_row.addWidget(self.speed_checkbox)

        buy_layout.addWidget(self.fs_checkbox, 0, 0)
        buy_layout.addWidget(self.sell_gear_checkbox, 0, 1)
        buy_layout.addLayout(epic_row, 1, 0, 1, 2)
        emulator_tab_layout.addWidget(buy_box)

        # Session stats
        self.session_box = QGroupBox('Session', self)
        self.stats_layout = QGridLayout(self.session_box)
        self.stats_layout.setHorizontalSpacing(14)
        # Two equal columns so the main stats sit in the same place with or without extras
        self.stats_layout.setColumnStretch(0, 1)
        self.stats_layout.setColumnStretch(2, 1)
        self.stat_labels = {}
        self.stat_values = {}
        for key, name in self.STATS:
            self.stat_labels[key] = QLabel(name, self)
            self.stat_values[key] = QLabel('<b>0</b>', self)
            self.stat_values[key].setAlignment(Qt.AlignmentFlag.AlignRight)
        emulator_tab_layout.addWidget(self.session_box)
        emulator_tab_layout.addStretch(1)

        # Current bot action
        self.status_field = QLabel(self)
        self.status_field.setStyleSheet('QLabel { background: white; border: 1px solid #c8c8c8; padding: 3px 6px; }')
        emulator_tab_layout.addWidget(self.status_field)

        # Buttons
        bottom_buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton('Start', self)
        self.refresh_button.clicked.connect(self.toggle_bot)
        bottom_buttons_layout.addWidget(self.refresh_button, 1)
        self.resume_button = QPushButton('Resume', self)
        self.resume_button.clicked.connect(self.resume_bot)
        self.resume_button.setVisible(False)
        bottom_buttons_layout.addWidget(self.resume_button, 1)
        emulator_tab_layout.addLayout(bottom_buttons_layout)

        self.setLayout(emulator_tab_layout)

        # Set initial state for option inputs
        self.change_option()
        self.change_epic_option()
        self.show_stats(['refreshes', 'bm', 'mm'])
        self.set_status('Idle', GREY)

        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.update_log)
        self.log_timer.setInterval(100)

    def set_status(self, text, color):
        self.status_field.setText(f'<span style="color:{color}; font-size:14px">●</span>&nbsp; {text}')

    def show_stats(self, keys):
        # Lay out only the stats that apply, the main ones on the left and the optional extras on the right
        for key, _ in self.STATS:
            self.stats_layout.removeWidget(self.stat_labels[key])
            self.stats_layout.removeWidget(self.stat_values[key])
            self.stat_labels[key].setVisible(key in keys)
            self.stat_values[key].setVisible(key in keys)
        main = [key for key in keys if key in ('refreshes', 'bm', 'mm')]
        extras = [key for key in keys if key not in main]
        for column, column_keys in enumerate((main, extras)):
            for row, key in enumerate(column_keys):
                self.stats_layout.addWidget(self.stat_labels[key], row, column * 2)
                self.stats_layout.addWidget(self.stat_values[key], row, column * 2 + 1)

    def change_option(self):
        is_limit = self.stop_dropdown.currentData() in ('ss', 'gold')
        self.amountInput.setPlaceholderText('0' if is_limit else 'No Limit')
        self.currentLabel.setText(f'Current {self.stop_dropdown.currentText()}')
        self.currentLabel.setVisible(is_limit)
        self.currentInput.setVisible(is_limit)
        self.currentInput.clear()

        # Gear prices vary so the gold limit can't account for them
        is_gold = self.stop_dropdown.currentData() == 'gold'
        if is_gold:
            self.sell_gear_checkbox.setChecked(False)
            if self.epic_dropdown.currentData() == 'buy':
                self.epic_dropdown.setCurrentIndex(0)
        self.sell_gear_checkbox.setEnabled(not is_gold)
        self.epic_dropdown.model().item(self.epic_dropdown.findData('buy')).setEnabled(not is_gold)

    def change_epic_option(self):
        # The minimum ES and speed only apply when buying
        is_buy = self.epic_dropdown.currentData() == 'buy'
        for widget in (self.minEsLabel, self.minEsInput, self.speed_checkbox):
            widget.setEnabled(is_buy)

    def resume_bot(self):
        if self.bot:
            self.bot.resume_event.set()

    def toggle_bot(self):
        if not self.refreshing:
            if not self.start_refreshing():
                return
        else:
            self.stop_refreshing()

        self.refreshing = not self.refreshing
        # Disable all inputs when refreshing
        is_buy = self.epic_dropdown.currentData() == 'buy'
        self.stop_dropdown.setEnabled(not self.refreshing)
        self.amountInput.setEnabled(not self.refreshing)
        self.currentInput.setEnabled(not self.refreshing)
        self.epic_dropdown.setEnabled(not self.refreshing)
        self.minEsInput.setEnabled(not self.refreshing and is_buy)
        self.speed_checkbox.setEnabled(not self.refreshing and is_buy)
        self.fs_checkbox.setEnabled(not self.refreshing)
        self.sell_gear_checkbox.setEnabled(not self.refreshing and self.stop_dropdown.currentData() != 'gold')

    def start_refreshing(self):
        # Get values from input fields
        currency = self.stop_dropdown.currentData()
        amount = int(self.amountInput.text() or 0)

        current = None
        if currency in ('ss', 'gold'):
            if not self.currentInput.text():
                self.set_status(f'Enter Your Current {self.stop_dropdown.currentText()}', RED)
                return False
            current = int(self.currentInput.text())

        config = {
            "ss": current if currency == 'ss' else None,
            "gold": current if currency == 'gold' else None,
            "fs": self.fs_checkbox.isChecked(),
            "gear": self.sell_gear_checkbox.isChecked(),
            "epic": {"mode": self.epic_dropdown.currentData(),
                     "min_es": int(self.minEsInput.text()) if self.minEsInput.text() else None,
                     "speed": self.epic_dropdown.currentData() == 'buy' and self.speed_checkbox.isChecked()},
            "stop_condition": {"currency": currency, "amount": amount},
        }

        self.bot = Bot(self.client, config)

        # Only show the stats for what's being bought
        stats = ['refreshes', 'bm', 'mm']
        if config["fs"]:
            stats.append('fs')
        if config["gear"]:
            stats.append('gear')
        if config["epic"]["mode"] == 'buy':
            stats.append('epic')
        self.show_stats(stats)

        self.worker_thread = worker(self.bot)
        self.worker_thread.emitFinished.connect(self.toggle_bot)

        self.worker_thread.start()
        self.last_toggle_time = time()
        self.was_paused = False
        self.log_timer.start()
        self.refresh_button.setText('Stop')
        return True

    def stop_refreshing(self):
        self.worker_thread.terminate()
        self.log_timer.stop()
        self.update_log()

        # Calculate stats
        bm_obtained = self.bot.currencies["bm"]["count"]
        mm_obtained = self.bot.currencies["mm"]["count"]
        # Left blank in the CSV when friendship points weren't being bought
        fs_obtained = self.bot.currencies["fs"]["count"] if "fs" in self.bot.currencies else ''
        gear_sold = self.bot.gear_sold if self.bot.gear else ''
        epic_bought = self.bot.epic_bought if self.bot.epic_mode == 'buy' else ''
        refreshes = self.bot.refreshes

        # Calculate time spent
        time_spent_seconds = time() - self.last_toggle_time
        hours, remainder = divmod(int(time_spent_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_spent = f'{hours:02}:{minutes:02}:{seconds:02}'

        # Show why the bot stopped
        if self.worker_thread.exception:
            self.set_status(f'Stopped: {self.worker_thread.exception}', RED)
        elif self.worker_thread.completed:
            self.set_status('Finished', GREY)
        else:
            self.set_status('Stopped', GREY)

        # Log stats to CSV file

        fieldnames = ['Date', 'Refreshes', 'Bookmarks', 'Mystic Medals', 'Friendship Points', 'Gear Sold', 'Epic Gear Bought', 'Time Spent']

        # Check if file exists to determine need to write headers
        file_exists = os.path.isfile('results.csv')
        if file_exists:
            upgrade_results_csv(fieldnames)

        current_date = datetime.now().strftime("%Y-%m-%d")

        with open('results.csv', 'a', newline='') as csvfile:
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
                'Friendship Points': fs_obtained,
                'Gear Sold': gear_sold,
                'Epic Gear Bought': epic_bought,
                'Time Spent': time_spent,
            })

        self.resume_button.setVisible(False)
        self.refresh_button.setText('Start')

    def update_log(self):
        # Update current skystones/gold field
        if self.bot.ss is not None:
            self.currentInput.setText(str(self.bot.ss))
        elif self.bot.gold is not None:
            self.currentInput.setText(str(self.bot.gold))

        # Runtime in the session box title
        elapsed_seconds = time() - self.last_toggle_time
        hours, remainder = divmod(int(elapsed_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.session_box.setTitle(f'Session  ·  {hours:02}:{minutes:02}:{seconds:02}')

        # Show progress towards the target for the stop condition currency
        stop_currency = self.bot.stop_condition["currency"]
        stop_amount = self.bot.stop_condition["amount"]
        values = {
            'refreshes': self.bot.refreshes,
            'bm': self.bot.currencies["bm"]["count"],
            'mm': self.bot.currencies["mm"]["count"],
            'fs': self.bot.currencies["fs"]["count"] if "fs" in self.bot.currencies else 0,
            'gear': self.bot.gear_sold,
            'epic': self.bot.epic_bought,
        }
        for key, value in values.items():
            text = f'{value}/{stop_amount}' if key == stop_currency and stop_amount else f'{value}'
            self.stat_values[key].setText(f'<b>{text}</b>')

        # Status line, flashing the taskbar when the bot first pauses
        if self.bot.paused:
            self.set_status(self.bot.status, AMBER)
            if not self.was_paused:
                QApplication.alert(self.window)
        else:
            self.set_status(self.bot.status, GREEN)
        self.was_paused = self.bot.paused
        self.resume_button.setVisible(self.bot.paused)


def upgrade_results_csv(fieldnames):
    # Rewrite results.csv with any new columns, leaving them blank for old rows
    with open('results.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        if reader.fieldnames == fieldnames:
            return
        rows = list(reader)

    with open('results.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class worker(QThread):
    emitFinished = pyqtSignal()

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.exception = None
        self.completed = False  # True when the bot stopped by itself rather than the stop button

    def run(self):
        try:
            self.bot.handle_refresh()
        except Exception as e:
            self.exception = e
        finally:
            self.completed = True
            self.emitFinished.emit()


def init():
    app = QApplication(sys.argv)
    app.setStyle('windowsvista')
    window = Window()
    window.show()
    sys.exit(app.exec())
