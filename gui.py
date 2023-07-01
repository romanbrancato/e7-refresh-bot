
import customtkinter

customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("green")

app = customtkinter.CTk()
app.title("e7 Refresh Bot")

table_frame = customtkinter.CTkFrame(app)
table_frame.pack(fill=customtkinter.BOTH, expand=True)


class Table:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.column_labels = [
            "Index",
            "Gold Limit",
            "SS Limit",
            "BM/BM Target (Rate)",
            "MM/MM Target (Rate)",
            "Refreshes"
        ]
        self.rows = []
        self.row_counter = len(self.rows) + 1

        for i, text in enumerate(self.column_labels):
            label = customtkinter.CTkLabel(self.parent_frame, text=text)
            label.grid(row=0, column=i + 1, padx=5, sticky="w")
        self.create_last_row()

    def add_row(self):
        # Create a new row
        new_row = Row(self.parent_frame, self.row_counter)
        self.rows.append(new_row)
        self.row_counter = len(self.rows)

        # Move the contents of the last row down
        for i, row_item in enumerate(self.rows[:6]):
            row_item.grid(row=self.row_counter)

        # Update the app's geometry to accommodate the new row
        app.update_idletasks()  # Wait for all pending tasks to complete
        width = self.parent_frame.winfo_reqwidth()
        height = self.parent_frame.winfo_reqheight()
        app.geometry(f"{width}x{height}")

    def create_last_row(self):
        add_emulator_button = customtkinter.CTkButton(self.parent_frame, text="Add Emulator", command=self.add_row)
        add_emulator_button.grid(row=self.row_counter, column=7, padx=5, pady=5)
        self.rows.append(add_emulator_button)

        entry_text = [
            "Index",
            "Gold Limit",
            "SS Limit",
            "BM Target",
            "MM Target",
        ]
        for i, text in enumerate(entry_text):
            entry = customtkinter.CTkEntry(self.parent_frame, placeholder_text=text)
            entry.grid(row=self.row_counter, column=i + 1, padx=5, sticky="w")
            self.rows.append(entry)


class Row:
    def __init__(self, parent_frame, row_number):
        self.parent_frame = parent_frame
        self.row_number = row_number
        self.columns = []

        self.create_columns()

    def create_columns(self):
        for i in range(8):
            if i == 7:
                delete = customtkinter.CTkButton(self.parent_frame, text="X", fg_color="red", hover_color="maroon", width=30, command=self.delete)
                delete.grid(row=self.row_number, column=i + 1, padx=5, pady=5)
                self.columns.append(delete)
            elif i == 6:
                button = customtkinter.CTkButton(self.parent_frame, text="Refresh", command=self.refresh)
                button.grid(row=self.row_number, column=i + 1, padx=5, pady=5)
                self.columns.append(button)
            else:
                label = customtkinter.CTkLabel(self.parent_frame, text="000")
                label.grid(row=self.row_number, column=i + 1, padx=5, pady=5, sticky="w")
                self.columns.append(label)

    def refresh(self):
        pass

    def delete(self):
        pass


table = Table(table_frame)

# Set the initial app's geometry based on the table frame's size
app.update()
width = table_frame.winfo_width()
height = table_frame.winfo_height()
app.geometry(f"{width}x{height}")

app.mainloop()
