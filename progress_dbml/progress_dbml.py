import tkinter as tk
from tkinter import filedialog
from progress import progress
from dbdiagramio import dbdiagramio

# Var Defs
root = tk.Tk()
root.withdraw()


def findTableByName(tables, name: str):
    i = 0
    for table in tables:
        if table.name == name:
            return i
        # Iterate
        i += 1
    # Nothing found
    return None


def main():
    file_path = filedialog.askopenfilename(filetypes=[("Progress DF Files", ".df")], title="Select Database File")
    save_path = filedialog.askdirectory(title="Select Save Location")

    if file_path == '':
        print("No file selected...")
        exit(0)

    pg_processor = progress.PG_Processor(file_path)
    tables = pg_processor.processFile()

    # Ask if the user wants to filter for a specific table
    should_filter = input("Do you want to filter for a specific table and it's first order foreign keys? Y/N\n")
    if should_filter == 'Y' or should_filter == 'y' or should_filter == 'Yes':
        # List options
        i = 1
        for table in tables:
            print(str(i) + ":  " + table.name)
            i += 1

        # Ask for selection
        filter_input = input('Enter table number to filter for (Blank to cancel filter): ')
        try:
            filter_index = int(filter_input) - 1
            if filter_index >= 0 and filter_index < len(tables):
                tables = pg_processor.filterByTable(tables[filter_index].name)
        except:
            pass

    # Generate DB Diagram IO File
    db_diag_io = dbdiagramio.DB_Diagram_IO(save_path)
    db_diag_io.convertFromPGTables(tables)


if __name__ == "__main__":
    main()
