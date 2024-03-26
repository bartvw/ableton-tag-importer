import os

import customtkinter
import tksheet
import csv
from adsrimporter import ADSRImporter

DEFAULT_DB_PATH = os.path.expanduser("~/Library/Application Support/ADSR/adsr_1_7.db3")
DEFAULT_DIRECTORY = os.path.expanduser("~/Music/Ableton/User Library/Samples")
MAPPING_CSV = "data.csv"


class AbletonTagImporter(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ableton Tag Importer")
        self.geometry("1100x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.csv_file = MAPPING_CSV
        self.db3_path = os.path.expanduser(DEFAULT_DB_PATH)
        if not os.path.exists(self.db3_path):
            self.db3_path = None

        self.directory_path = None
        self.mapping_list = []
        self.unmapped_tags = []
        self.mapping_changed = False

        self.load_mapping()

        # Path to db3 file
        self.db3_label = customtkinter.CTkLabel(
            self, text="DB3 File Path: " + self.db3_path
        )
        self.db3_label.grid(row=0, column=0, pady=10)
        self.db3_button = customtkinter.CTkButton(
            self, text="Select...", command=self.open_db3_selection
        )
        self.db3_button.grid(row=0, column=1, pady=10)

        # Directory picker
        self.directory_label = customtkinter.CTkLabel(self, text="Directory to Sync: ")
        self.directory_label.grid(row=1, column=0, pady=10)
        self.directory_button = customtkinter.CTkButton(
            self, text="Select...", command=self.open_directory_selection
        )
        self.directory_button.grid(row=1, column=1, pady=10)

        self.logbox = customtkinter.CTkTextbox(self)
        self.logbox.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.logbox.configure(state="disabled")

        # Sync button
        self.sync_button = customtkinter.CTkButton(self, text="Sync", command=self.sync)
        self.sync_button.configure(state="disabled")
        self.sync_button.grid(row=3, column=0, columnspan=2, pady=10)

        table_frame = customtkinter.CTkFrame(self)
        table_frame.grid(row=0, column=2, rowspan=3, sticky="nsew")
        self.table = tksheet.Sheet(
            table_frame,
            headers=["Source", "Destination"],
            total_columns=2,
            show_row_index=False,
            default_row_index_width=0,
        )
        self.table.set_options(auto_resize_columns=400)
        self.table.pack(fill="both", expand=True)
        self.table.enable_bindings(
            "single_select",
            "row_select",
            "drag_select",
            "column_width_resize",
            "arrowkeys",
            "right_click_popup",
            "rc_select",
            "rc_insert_column",
            "rc_delete_column",
            "rc_delete_row",
            "copy",
            "paste",
            "delete",
            "undo",
            "redo",
            "edit_cell",
        )
        self.table.span("A").readonly()

        self.table.set_sheet_data(self.mapping_list)
        self.table.bind("<<SheetModified>>", self.table_updated)

    def log(self, message):
        self.logbox.configure(state="normal")
        self.logbox.insert("end", message + "\n")
        self.logbox.configure(state="disabled")

    def table_updated(self, event):
        self.save_mapping()

    def load_mapping(self):
        try:
            with open(self.csv_file, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) > 1:
                        self.mapping_list.append(row)
                    elif len(row) == 1:
                        self.mapping_list.append([row[0], None])
            self.mapping_list = sorted(self.mapping_list, key=lambda x: x[0])
            self.mapping_changed = False
        except FileNotFoundError:
            pass

    def save_mapping(self):
        with open(self.csv_file, "w", encoding="utf-8") as file:
            writer = csv.writer(file)
            for key, value in self.mapping_list:
                writer.writerow([key, value if value is not None else ""])

    def open_directory_selection(self):
        self.directory_path = customtkinter.filedialog.askdirectory(
            initialdir=(
                self.directory_path
                if self.directory_path is not None
                else DEFAULT_DIRECTORY
            ),
            mustexist=True,
        )
        self.directory_label.configure(text="Directory to Sync: " + self.directory_path)
        self.sync(dry_run=True)
        self.sync_button.configure(state="normal")

    def open_db3_selection(self):
        self.db3_path = customtkinter.filedialog.askopenfilename(
            initialfile=os.path.basename(self.db3_path),
            initialdir=os.path.dirname(self.db3_path),
            filetypes=[("DB3 Files", "*.db3")],
        )
        self.db3_label.configure(text="DB3 File Path: " + self.db3_path)

    def log_tag_event(self, event):
        self.log(f"Added tag '{event['tag']}' to '{event['file_path']}'")

    def sync(self, dry_run=False):
        if not self.directory_path:
            self.log("No directory selected")
            return

        mapping = {row[0]: row[1] for row in self.mapping_list}
        sync = ADSRImporter(self.db3_path, mapping)

        # TODO: We should really run this on a separate thread
        num_imported_tags, unmapped = sync.sync_directory(
            self.directory_path, dry_run=dry_run, on_tag_added=self.log_tag_event
        )

        for tag in unmapped:
            if tag not in mapping:
                self.add_to_mapping(tag)

        self.table.set_sheet_data(
            self.mapping_list, keep_formatting=False, reset_highlights=True
        )

        for tag in unmapped:
            for i, row in enumerate(self.mapping_list):
                if tag in row:
                    self.table.highlight_cells(row=i, column=1, bg="red")
                    break

        self.log(f"Directory: {self.directory_path}")
        self.log(f"{num_imported_tags} tags imported")
        self.log("Unmapped Tags:")
        for tag in unmapped:
            self.log(" * " + tag)

        print(unmapped)

    def add_to_mapping(self, tag):
        for i, row in enumerate(self.mapping_list):
            if tag <= row[0]:
                if tag != row[0]:
                    self.mapping_list.insert(i, [tag, None])
                    self.mapping_changed = True
                    break
        else:
            self.mapping_list.append([tag, None])
            self.mapping_changed = True


app = AbletonTagImporter()
app.mainloop()
