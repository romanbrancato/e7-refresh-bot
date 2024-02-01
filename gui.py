import sys
from datetime import timedelta
from time import time

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QPushButton, QLabel,
    QTextBrowser, QInputDialog, QMessageBox, QLineEdit, QCheckBox, QFormLayout,
    QHBoxLayout, QFrame, QRadioButton, QButtonGroup, QGridLayout, QDoubleSpinBox
)
from PyQt6.QtGui import QIcon, QIntValidator

from bot import Bot
from client import Client, adb_connect_all, adb_disconnect_all
from detection import scan


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.active_devices = []

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget(self)
        main_layout.addWidget(self.tab_widget)

        # Info Tab
        info_tab = InfoTab(self.update_delay)
        self.tab_widget.addTab(info_tab, 'Info')
        self.tab_widget.setGeometry(5, 5, 300, 490)

        # Add emulator button
        add_emulator_button = QPushButton('Add Emulator Instance', self)
        add_emulator_button.clicked.connect(self.add_emulator_button_event)
        main_layout.addWidget(add_emulator_button)

        # Window Properties
        self.resize(316, 460)
        self.setWindowTitle('e7 Refresh Bot')
        icon_path = 'images\\covenant_bookmark.ico'
        self.setWindowIcon(QIcon(icon_path))

        self.setLayout(main_layout)

    def add_emulator_button_event(self):
        # Get the list of connected emulators
        emulator_list = adb_connect_all()
        emulator_list = [emulator for emulator in emulator_list if emulator not in self.active_devices]
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
                new_tab = EmulatorTab(client, self.delete_tab)
                # Insert the new tab
                self.tab_widget.insertTab(0, new_tab, f'{emulator}')
                # Focus on the new tab
                self.tab_widget.setCurrentIndex(0)
                # Add device to currently connected devices
                self.active_devices.append(emulator)

    def update_delay(self, delay):
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if isinstance(tab, EmulatorTab):
                tab.delay = delay
                if tab.bot:
                    tab.bot.delay = delay

    def delete_tab(self, client):
        self.active_devices.remove(client.address)
        self.tab_widget.removeTab(self.tab_widget.currentIndex())

    def closeEvent(self, event):
        adb_disconnect_all()
        event.accept()


class InfoTab(QWidget):
    def __init__(self, update_delay_callback):
        super().__init__()
        self.update_delay_callback = update_delay_callback
        info_tab_layout = QVBoxLayout(self)

        # Text Display
        info_layout = QVBoxLayout()
        self.info_text_field = QTextBrowser(self)
        self.info_text_field.setPlainText(
            "Click 'Add Emulator Instance' to begin\n"
            "(Currently only supports LDPlayer)\n\n"
            "Notes:\n\n"
            "For the bot to work:\n"
            "- Resolution: 960x540(dpi 160)\n"
            "- ADB debugging: Open local connection\n"
            "- Preferably enable 'Fixed Window Size'\n\n"
            "* Emulators will appear as their adb serial i.e an LDPLayer instance at index 0 will appear as 127.0.0.1:5555\n\n"
            "* If you notice the bot missing currencies due to lag, increase the delay (0.3 is default)")
        info_layout.addWidget(self.info_text_field)

        # Delay Setting
        global_option_layout = QGridLayout(self)
        self.delayInputLabel = QLabel('Delay (secs)')
        self.delay_input = QDoubleSpinBox(self)
        self.delay_input.setDecimals(1)
        self.delay_input.setSingleStep(0.1)
        self.delay_input.setMaximum(2.0)
        self.delay_input.setValue(0.3)
        self.delay_input.valueChanged.connect(self.update_delay)
        self.delay_input.setAlignment(Qt.AlignmentFlag.AlignRight)
        global_option_layout.addWidget(self.delayInputLabel, 0, 0)
        global_option_layout.addWidget(self.delay_input, 0, 1)
        info_layout.addLayout(global_option_layout)

        # Image Link
        github_icon = QLabel(self)
        github_icon.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        github_icon.setText(
            '<a href="https://github.com/romanbrancato/e7-refresh-bot"><img src="images/github.png"/></a>')
        github_icon.setOpenExternalLinks(True)
        info_layout.addWidget(github_icon)

        info_tab_layout.addLayout(info_layout)

    def update_delay(self):
        self.update_delay_callback(self.delay_input.value())


class EmulatorTab(QWidget):
    def __init__(self, client, delete_callback):
        super().__init__()
        self.client = client
        self.delete_callback = delete_callback

        self.bot = None
        self.delay = 0.3
        self.worker_thread = None
        self.refreshing = False
        self.last_toggle_time = None

        emulator_tab_layout = QVBoxLayout(self)
        int_validator = QIntValidator(self)

        # Input for Gold and Skystones
        gold_ss_layout = QFormLayout(self)
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
        scan_button_layout = QHBoxLayout(self)
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
        option_layout = QGridLayout(self)
        option_layout.setContentsMargins(45, 0, 45, 0)

        # Check Box
        self.dispatch_checkbox = QCheckBox('Auto Dispatch Retry', self)

        # Radio Buttons
        self.radio_button_group = QButtonGroup(self)
        self.bmButton = QRadioButton('Bookmarks')
        self.bmButton.clicked.connect(self.change_option)
        self.bmButton.setChecked(True)
        self.radio_button_group.addButton(self.bmButton, 0)

        self.mmButton = QRadioButton('Mystic Medals')
        self.mmButton.clicked.connect(self.change_option)
        self.radio_button_group.addButton(self.mmButton, 1)

        self.ssButton = QRadioButton('Skytones')
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

        option_layout.addWidget(self.dispatch_checkbox, 0, 0, 1, 2)
        option_layout.addWidget(self.bmButton, 1, 0)
        option_layout.addWidget(self.bmTargetInput, 1, 1)
        option_layout.addWidget(self.mmButton, 2, 0)
        option_layout.addWidget(self.mmTargetInput, 2, 1)
        option_layout.addWidget(self.ssButton, 3, 0)
        option_layout.addWidget(self.ssLimitInput, 3, 1)
        emulator_tab_layout.addLayout(option_layout)

        # Text Display
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(45, 0, 45, 0)
        self.log_text_field = QTextBrowser(self)
        log_layout.addWidget(self.log_text_field)
        emulator_tab_layout.addLayout(log_layout)

        # Buttons
        bottom_buttons_layout = QHBoxLayout(self)
        bottom_buttons_layout.setContentsMargins(45, 0, 45, 0)
        self.remove_button = QPushButton('Remove', self)
        self.remove_button.clicked.connect(self.remove_tab)
        bottom_buttons_layout.addWidget(self.remove_button)
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

    def remove_tab(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
        self.delete_callback(self.client)

    def toggle_bot(self):
        # Start Refreshing
        if not self.refreshing:

            self.bot = Bot(self.client, self.delay, self.get_values())
            self.worker_thread = worker(self.bot)
            self.worker_thread.emitFinished.connect(self.toggle_bot)

            self.worker_thread.start()
            self.last_toggle_time = time()
            self.log_timer.start()
            self.refresh_button.setText('Stop')

        # Stop Refreshing
        else:
            self.worker_thread.terminate()
            self.log_timer.stop()

            if self.worker_thread.exception:
                self.log_text_field.append(f'Stopped')
                self.log_text_field.append(f'- Reason: {self.worker_thread.exception}')
            else:
                self.log_text_field.append(f'Finished')
            self.log_text_field.append(f'- Gold Spent: {self.bot.gold_start - self.bot.gold}')
            self.log_text_field.append(f'- Skystones Spent: {self.bot.ss_start - self.bot.ss}')

            self.refresh_button.setText('Refresh')

        self.refreshing = not self.refreshing
        self.scan_button.setEnabled(not self.refreshing)
        self.dispatch_checkbox.setEnabled(not self.refreshing)
        self.change_option()

    def update_log(self):
        self.goldInput.setText(str(self.bot.gold))
        self.ssInput.setText(str(self.bot.ss))
        self.log_text_field.clear()

        runtime = timedelta(seconds=time() - self.last_toggle_time)
        hours, remainder = divmod(runtime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        runtime = f'{hours:02}:{minutes:02}:{seconds:02}'
        self.log_text_field.append(f'Refreshing {runtime}')

        bm_count = self.bot.currencies["bm"]["count"]
        mm_count = self.bot.currencies["mm"]["count"]
        stop_currency = self.bot.stop_condition["currency"]
        stop_amount = self.bot.stop_condition["amount"]

        bookmarks_str = f'{bm_count}/{stop_amount}' if stop_currency == "bm" and stop_amount != 0 else f'{bm_count}'
        mystic_medals_str = f'{mm_count}/{stop_amount}' if stop_currency == "mm" and stop_amount != 0 else f'{mm_count}'

        self.log_text_field.append(f'- Bookmarks: {bookmarks_str}')
        self.log_text_field.append(f'- Mystic Medals: {mystic_medals_str}')
        self.log_text_field.append(f'- Refreshes: {self.bot.refreshes}')

    def get_values(self):
        stop_condition = self.radio_button_group.checkedId()
        currency = "bm" if stop_condition == 0 else "mm" if stop_condition == 1 else "ss"
        amount = self.bmTargetInput.text() if stop_condition == 0 else self.mmTargetInput.text() if stop_condition == 1 else self.ssLimitInput.text()
        return {
            "gold": int(self.goldInput.text() or 0),
            "ss": int(self.ssInput.text() or 0),
            "auto_dispatch": self.dispatch_checkbox.isChecked(),
            "stop_condition": {"currency": currency, "amount": int(amount or 0)}
        }


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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
