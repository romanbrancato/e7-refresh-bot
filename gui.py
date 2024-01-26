import threading
import customtkinter
from bot import Bot
from ldplayer.client import Client


class App:
    def __init__(self):
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")

        self.root = customtkinter.CTk()
        self.root.resizable(False, False)
        self.root.iconbitmap("detection\\images\\covenant_bookmark.ico")
        self.root.title("e7 Refresh Bot")

        self.table_frame = customtkinter.CTkFrame(self.root)
        self.table_frame.pack(fill=customtkinter.BOTH, expand=True)
        self.table = Table(self.table_frame, self)

        self.root.mainloop()

    def update_window_geometry(self):
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        self.root.geometry(f"{width}x{height}")


class Table:
    COLUMN_LABELS = [
        "Instance Index",
        "Bookmarks/Target",
        "Mystic Medals/Target",
        "Refreshes"
    ]
    ENTRY_TEXT = [
        "Instance Index",
        "Bookmark Target",
        "Mystic Medal Target"
    ]

    def __init__(self, parent_frame, app):
        self.parent_frame = parent_frame
        self.app = app
        self.rows = []
        self.row_counter = len(self.rows) + 1

        for i, text in enumerate(self.COLUMN_LABELS):
            label = customtkinter.CTkLabel(self.parent_frame, text=text)
            label.grid(row=0, column=i + 1, padx=5, sticky="w")
        self.add_emulator_row()

    def add_emulator_row(self):
        add_emulator_button = customtkinter.CTkButton(self.parent_frame, text="Add Emulator", command=self.add_emulator)
        add_emulator_button.grid(row=self.row_counter, column=5, padx=5, pady=5)
        self.rows.append(add_emulator_button)

        for i, text in enumerate(self.ENTRY_TEXT):
            entry = customtkinter.CTkEntry(self.parent_frame, placeholder_text=text)
            entry.grid(row=self.row_counter, column=i + 1, padx=5, sticky="w")
            self.rows.append(entry)

    def add_emulator(self):
        # Create client and bot instances
        client = Client(str(self.get_values()[0]))
        bot = Bot(client, *self.get_values()[1:3])

        # Create new row
        new_row = Row(self.parent_frame, self.row_counter, bot, self.delete_row)
        self.rows.append(new_row)
        self.row_counter = len(self.rows)

        # Shift contents of last row down
        for row_item in self.rows[:4]:
            row_item.grid(row=self.row_counter)

        # Update the app's geometry to accommodate new row
        self.app.update_window_geometry()

    def get_values(self):
        entry_values = [int(entry.get()) if entry.get() != '' else 0 for entry in self.rows if
                        isinstance(entry, customtkinter.CTkEntry)][-3:]

        for value, name in zip(entry_values, ['Index', 'Bookmark Target', 'Mystic Medal Target']):
            if value < 0:
                raise ValueError(f"{name} must be a non-negative integer.")

        return entry_values

    def delete_row(self, row):
        self.rows.remove(row)

        # Destroy the row's widgets
        for widget in row.columns:
            widget.destroy() if widget.winfo_exists() else None

        row.columns.clear()
        self.row_counter = len(self.rows)
        self.app.update_window_geometry()


class Row:
    def __init__(self, parent_frame, row_number, bot, delete_callback):
        self.parent_frame = parent_frame
        self.row_number = row_number
        self.bot = bot
        self.delete_callback = delete_callback

        self.columns = []
        self.create_columns()

        self.thread = None

        self.update_interval = 100
        self.refresh_state = self.bot.refreshing
        self.update_row()

    def create_columns(self):
        for i in range(6):
            if i == 5:
                delete = customtkinter.CTkButton(self.parent_frame, text="X", fg_color="transparent",
                                                 hover_color="maroon", width=30, command=self.delete)
                delete.grid(row=self.row_number, column=i + 1, padx=5, pady=5)
                self.columns.append(delete)
            elif i == 4:
                button = customtkinter.CTkButton(self.parent_frame, text="Refresh", command=self.toggle_bot_status)
                button.grid(row=self.row_number, column=i + 1, padx=5, pady=5)
                self.columns.append(button)
            else:
                label = customtkinter.CTkLabel(self.parent_frame, text="0")
                label.grid(row=self.row_number, column=i + 1, padx=5, pady=5, sticky="w")
                self.columns.append(label)

    def delete(self):
        if self.bot.refreshing:
            self.bot.refreshing = False
            self.thread.join()
            self.parent_frame.after_cancel(self.update_row)
        self.delete_callback(self)

    def toggle_bot_status(self):
        if not self.thread:
            # Create a new thread
            self.thread = threading.Thread(target=self.bot.handle_refresh)

        if self.bot.refreshing:
            self.bot.refreshing = False
            self.thread.join()
            self.parent_frame.after_cancel(self.update_row)
            self.thread = None

        else:
            self.bot.refreshing = True
            self.thread.start()
            self.update_row()

    def update_row(self):
        values = [
            self.bot.client.emulator_index,
            f"{self.bot.currencies['bm']['count']}/{self.bot.bookmark_target}",
            f"{self.bot.currencies['mm']['count']}/{self.bot.mystic_medal_target}",
            self.bot.refreshes
        ]

        button_color, button_text, button_hover = ("red", "Stop", "maroon") if self.bot.refreshing else (
            ["#2CC985", "#2FA572"], "Refresh", ["#0C955A", "#106A43"]
        )

        for i, label in enumerate(self.columns[:4]):
            label.configure(text=values[i])

        if self.refresh_state is not self.bot.refreshing:
            self.columns[4].configure(text=button_text, fg_color=button_color, hover_color=button_hover)
            self.refresh_state = self.bot.refreshing

        self.parent_frame.after(self.update_interval, self.update_row)


app = App()
