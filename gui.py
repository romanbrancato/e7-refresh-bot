import threading
import customtkinter
from bot import Bot
from client import Client


class App:
    def __init__(self):
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")

        self.app = customtkinter.CTk()
        self.app.title("e7 Refresh Bot")

        self.table_frame = customtkinter.CTkFrame(self.app)
        self.table_frame.pack(fill=customtkinter.BOTH, expand=True)
        self.table = Table(self.table_frame, self)

        self.update_geometry()

        self.app.mainloop()

    def update_geometry(self):
        self.app.update_idletasks()
        width = self.app.winfo_reqwidth()
        height = self.app.winfo_reqheight()
        self.app.geometry(f"{width}x{height}")


class Table:
    def __init__(self, parent_frame, app):
        self.parent_frame = parent_frame
        self.app = app
        self.column_labels = [
            "Index",
            "Gold/Limit",
            "SS/Limit",
            "BM/Target",
            "MM/Target",
            "Refreshes"
        ]
        self.rows = []
        self.row_counter = len(self.rows) + 1

        for i, text in enumerate(self.column_labels):
            label = customtkinter.CTkLabel(self.parent_frame, text=text)
            label.grid(row=0, column=i + 1, padx=5, sticky="w")
        self.create_last_row()

    def add_emulator(self):

        values = self.get_values()

        # Create client, bot, and thread instances
        client = Client(values[0])
        bot = Bot(client, values[1], values[2], values[3], values[4], values[5], values[6])

        thread = threading.Thread(target=bot.handle_refresh)

        # Create a new row
        new_row = Row(self.parent_frame, self.row_counter, bot, thread)
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

        entry_text = [
            "Index",
            "Gold/Limit",
            "SS/Limit",
            "BM Target",
            "MM Target"
        ]
        for i, text in enumerate(entry_text):
            entry = customtkinter.CTkEntry(self.parent_frame, placeholder_text=text)
            entry.grid(row=self.row_counter, column=i + 1, padx=5, sticky="w")
            self.rows.append(entry)

    def get_values(self):
        entry_values = [entry.get() for entry in self.rows[:] if isinstance(entry, customtkinter.CTkEntry)]

        # Assign values to variables
        index, gold, ss, bm_target, mm_target = entry_values[-5:]
        gold_amount, gold_limit = gold.split("/")
        ss_amount, ss_limit = ss.split("/")

        return [index, int(gold_amount), int(gold_limit), int(ss_amount), int(ss_limit), int(bm_target), int(mm_target)]


class Row:
    def __init__(self, parent_frame, row_number, bot, thread):
        self.parent_frame = parent_frame
        self.row_number = row_number
        self.bot = bot
        self.thread = thread

        self.columns = []
        self.create_columns()

        self.update_labels()

    def create_columns(self):
        for i in range(8):
            if i == 7:
                delete = customtkinter.CTkButton(self.parent_frame, text="X", fg_color="transparent",
                                                 hover_color="maroon", width=30, command=self.delete)
                delete.grid(row=self.row_number, column=i + 1, padx=5, pady=5)
                self.columns.append(delete)
            elif i == 6:
                button = customtkinter.CTkButton(self.parent_frame, text="Refresh", command=self.refresh)
                button.grid(row=self.row_number, column=i + 1, padx=5, pady=5)
                self.columns.append(button)
            else:
                label = customtkinter.CTkLabel(self.parent_frame, text="0")
                label.grid(row=self.row_number, column=i + 1, padx=5, pady=5, sticky="w")
                self.columns.append(label)

    def refresh(self):
        self.thread.start()

    def delete(self):
        # Stop the bot thread before deleting the row
        if self.thread:
            self.thread.stop()  # Add a stop method to your Bot class to gracefully stop the bot
            self.bot_thread.join()  # Wait for the thread to finish

        # Delete the row

    def update_labels(self):
        values = [
            self.bot.client.index,
            str(self.bot.g),
            str(self.bot.g_limit),
            str(self.bot.ss),
            str(self.bot.ss_limit),
            str(self.bot.bm),
            str(self.bot.bm_target),
            str(self.bot.mm),
            str(self.bot.mm_target),
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


app = App()
