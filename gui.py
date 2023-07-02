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
            "BM/Target (Rate)",
            "MM/Target (Rate)",
            "Refreshes"
        ]
        self.rows = []
        self.row_counter = len(self.rows) + 1

        for i, text in enumerate(self.column_labels):
            label = customtkinter.CTkLabel(self.parent_frame, text=text)
            label.grid(row=0, column=i + 1, padx=5, sticky="w")
        self.create_last_row()

    def add_emulator(self):
        # Get the values from the entry fields
        entry_values = [entry.get() for entry in self.rows[:] if
                        isinstance(entry, customtkinter.CTkEntry)]

        # Assign values to variables
        index, gold_limit, ss_limit, bm_target, mm_target = entry_values[-5:]
        gold_amount, gold_limit = gold_limit.split("/")
        ss_amount, ss_limit = ss_limit.split("/")

        # Create client and bot instances
        client = Client(index)
        bot = Bot(client, int(gold_amount), int(ss_amount), int(gold_limit), int(ss_limit), int(bm_target),
                  int(mm_target))

        # Create a new row
        new_row = Row(self.parent_frame, self.row_counter, bot)
        self.rows.append(new_row)
        self.row_counter = len(self.rows)

        new_row.update_labels([index, gold_limit, ss_limit, bm_target, mm_target])

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


class Row:
    def __init__(self, parent_frame, row_number, bot):
        self.parent_frame = parent_frame
        self.row_number = row_number
        self.bot = bot
        self.columns = []

        self.create_columns()

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
        self.bot.handle_refresh()

    def delete(self):
        pass

    def update_labels(self, values):
        for i, value in enumerate(values):
            if i < len(self.columns) - 2:
                label = self.columns[i]
                label.configure(text=value)


app = App()
