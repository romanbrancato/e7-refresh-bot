import threading
import customtkinter
from bot import Bot
from client import Client
from util import validate_fraction


class App:
    def __init__(self):
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")

        self.root = customtkinter.CTk()
        self.root.iconbitmap("detection\\reference_images\\covenant_bookmark.ico")
        self.root.title("e7 Refresh Bot")

        self.table_frame = customtkinter.CTkFrame(self.root)
        self.table_frame.pack(fill=customtkinter.BOTH, expand=True)
        self.table = Table(self.table_frame, self)

        self.update_geometry()

        self.root.mainloop()

    def update_geometry(self):
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        self.root.geometry(f"{width}x{height}")


class Table:
    COLUMN_LABELS = [
        "LDPlayer Index",
        "Gold/Limit",
        "Skystones/Limit",
        "Bookmarks/Target",
        "Mystic Medals/Target",
        "Refreshes"
    ]
    ENTRY_TEXT = [
        "LDPLayer Index",
        "Gold/Limit",
        "Skystones/Limit",
        "Bookmark Target",
        "Mystic Medal Target"
    ]

    def __init__(self, parent_frame, app):
        self.parent_frame = parent_frame
        self.app = app
        self.rows = []
        self.row_counter = 1

        for i, text in enumerate(self.COLUMN_LABELS):
            label = customtkinter.CTkLabel(self.parent_frame, text=text)
            label.grid(row=0, column=i + 1, padx=5, sticky="w")
        self.create_last_row()

    def add_emulator(self):
        values = self.get_values()

        # Create client, bot, and thread instances
        client = Client(values[0])
        bot = Bot(client, values[1], values[2], values[3], values[4], values[5], values[6])

        # Create a new row
        new_row = Row(self.parent_frame, self.row_counter, bot, self.delete_row)
        self.rows.append(new_row)
        self.row_counter = len(self.rows)

        # Move the contents of the last row down
        for i, row_item in enumerate(self.rows[:6]):
            row_item.grid(row=self.row_counter)

        # Update the app's geometry to accommodate the new row
        self.app.update_geometry()

    def create_last_row(self):
        add_emulator_button = customtkinter.CTkButton(self.parent_frame, text="Add Emulator", command=self.add_emulator)
        add_emulator_button.grid(row=self.row_counter, column=7, padx=5, pady=5)
        self.rows.append(add_emulator_button)

        for i, text in enumerate(self.ENTRY_TEXT):
            entry = customtkinter.CTkEntry(self.parent_frame, placeholder_text=text)
            entry.grid(row=self.row_counter, column=i + 1, padx=5, sticky="w")
            self.rows.append(entry)

    def get_values(self):
        entry_values = [entry.get() for entry in self.rows if isinstance(entry, customtkinter.CTkEntry)]

        # Assign values to variables
        index, gold, ss, bm_target, mm_target = entry_values[-5:]
        gold_amount, gold_limit = validate_fraction(gold)
        ss_amount, ss_limit = validate_fraction(ss)

        return [index, int(gold_amount), int(gold_limit), int(ss_amount), int(ss_limit), int(bm_target), int(mm_target)]

    def delete_row(self, row):
        # Remove the row from the list
        self.rows.remove(row)

        # Destroy the row's widgets
        for widget in row.columns:
            widget.destroy()

        self.row_counter = len(self.rows)

        # Update the app's geometry
        self.app.update_geometry()


class Row:
    def __init__(self, parent_frame, row_number, bot, delete_callback):
        self.parent_frame = parent_frame
        self.row_number = row_number
        self.bot = bot
        self.delete_callback = delete_callback

        self.columns = []
        self.create_columns()

        self.update_interval = 100
        self.update_labels()

        self.thread = None

    def create_columns(self):
        for i in range(8):
            if i == 7:
                delete = customtkinter.CTkButton(self.parent_frame, text="X", fg_color="transparent",
                                                 hover_color="maroon", width=30, command=self.delete)
                delete.grid(row=self.row_number, column=i + 1, padx=5, pady=5)
                self.columns.append(delete)
            elif i == 6:
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
            self.parent_frame.after_cancel(self.update_labels_loop)
        self.delete_callback(self)

    def toggle_bot_status(self):
        if not self.thread:
            # Create a new thread
            self.thread = threading.Thread(target=self.bot.handle_refresh)

        if self.bot.refreshing:
            # Stop if the bot is running
            self.bot.refreshing = False
            self.thread.join()
            self.parent_frame.after_cancel(self.update_labels_loop)
            self.thread = None
        else:
            # Start if the bot is not running
            self.bot.refreshing = True
            self.thread.start()
            self.update_labels_loop()

        # Update the button's color and text based on the bot status
        button_color = "red" if self.bot.refreshing else ["#2CC985", "#2FA572"]
        button_text = "Stop" if self.bot.refreshing else "Refresh"
        button_hover = "maroon" if self.bot.refreshing else ["#0C955A", "#106A43"]
        self.columns[6].configure(text=button_text, fg_color=button_color, hover_color=button_hover)

    def update_labels(self):
        values = [
            self.bot.client.emulator_index,
            str(self.bot.current_gold),
            str(self.bot.gold_limit),
            str(self.bot.current_skystones),
            str(self.bot.skystone_limit),
            str(self.bot.bookmarks),
            str(self.bot.bookmark_target),
            str(self.bot.mystic_medals),
            str(self.bot.mystic_medal_target),
            str(self.bot.refreshes)
        ]

        label_mappings = {
            0: lambda: values[0],
            1: lambda: f"{values[1]}/{values[2]}",
            2: lambda: f"{values[3]}/{values[4]}",
            3: lambda: f"{values[5]}/{values[6]}",
            4: lambda: f"{values[7]}/{values[8]}",
            5: lambda: values[9]
        }

        for i in range(6):
            label = self.columns[i]
            label.configure(text=label_mappings[i]())

    def update_labels_loop(self):
        self.update_labels()

        # Schedule the next update after the specified interval
        self.parent_frame.after(self.update_interval, self.update_labels_loop)


app = App()
