"""
Name: AwesomeNova
Updated at: 10/17/2024

Script for converting Aleae files into MARlea ones and vice versa via sequential or pipelined execution. Please read the
README to learn how to use it. The script checks for whether an input file given to it is valid, specified by the
documentation for Aleae and MARlea, if and only if the user enables it. Any converted file will be valid if a given
input file or set of files is valid.

There are no major bugs found in the code at the moment. However, if you encountered a bug or issue while using this script,
please send an issue on the GitHub repo or push a fix of the code on a separate branch and make a pull request.
"""
import argparse
import os.path
import os
import sys
import csv
import queue
import tkinter
from enum import IntEnum
from threading import Thread
from tkinter import Tk, ttk, StringVar, BooleanVar, filedialog, messagebox, W

ALEAE_FIELD_SEPARATOR = ':'
MARLEA_TERM_SEPARATOR = '+'
MARLEA_ARROW = "=>"
MARLEA_NULL = 'NULL'

input_file_reader_to_converter_queue = queue.Queue()                  # Setup queues for inter-thread communication
input_file_reader_to_output_writer_queue = queue.Queue()
input_file_reader_to_converter_auxilliary_queue = queue.Queue()
converter_to_output_file_writer_queue_0 = queue.Queue()
converter_to_output_file_writer_queue_1 = queue.Queue()
END_PROCEDURE = "fin"


class ReactionParts(IntEnum):
    REACTANTS = 0
    PRODUCTS = 1
    REACTION_RATE = 2
    NUM_FIELDS = 3


gui_root = Tk()                                                        # Setup the gui
gui_root.title("Aleae-MARlea File Converter")
gui_root.minsize(500, 300)
selected_in_file_label = ttk.Label(gui_root, text="Selected File:")
selected_r_file_label = ttk.Label(gui_root, text="Selected File:")
selected_marlea_file_label = ttk.Label(gui_root, text="Selected File:")
input_label = ttk.Label(gui_root, text="Input Files")
output_label = ttk.Label(gui_root, text="Output Files")
waste_label = ttk.Label(gui_root, text="Waste:")
aether_label = ttk.Label(gui_root, text="Aether:")

gui_input_mode = StringVar()

gui_a_to_m_aleae_file_in = ""                                           # Initialize gui file variables
gui_a_to_m_aleae_file_r = ""
gui_a_to_m_marlea_file = StringVar()

gui_m_to_a_marlea_file = ""
gui_m_to_a_aleae_file_in = StringVar()
gui_m_to_a_aleae_file_r = StringVar()

gui_error_check_enable=BooleanVar()
gui_pipeline_enable=BooleanVar()

gui_waste=StringVar()
gui_aether=StringVar()

mainframe = ttk.Frame(gui_root, padding="6 6 24 24")
mainframe.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
gui_root.columnconfigure(0, weight=10)
gui_root.columnconfigure(1, weight=10)
gui_root.columnconfigure(2, weight=10)
gui_root.rowconfigure(list(range(10)), weight=10)


def open_file_dialog_in():
    """Prompt the user with a open file dialog and set the .in file variable to user input."""
    global gui_a_to_m_aleae_file_in
    gui_a_to_m_aleae_file_in = filedialog.askopenfilename(title="Select a File", filetypes=[("Aleae initialization files", "*.in")])
    if gui_a_to_m_aleae_file_in:
        selected_in_file_label.config(text=f"Selected File: {gui_a_to_m_aleae_file_in}")

def open_file_dialog_r():
    """Prompt the user with an open file dialog and set the .r file variable to user input."""
    global gui_a_to_m_aleae_file_r
    gui_a_to_m_aleae_file_r = filedialog.askopenfilename(title="Select a File", filetypes=[("Aleae reaction files", "*.r")])
    if gui_a_to_m_aleae_file_r:
        selected_r_file_label.config(text=f"Selected File: {gui_a_to_m_aleae_file_r}")

def open_file_dialog_csv():
    """Prompt the user with a open file dialog and set the .csv file variable to user input."""
    global gui_m_to_a_marlea_file
    gui_m_to_a_marlea_file = filedialog.askopenfilename(title="Select a File", filetypes=[("MARlea files", "*.csv")])
    if gui_m_to_a_marlea_file:
        selected_marlea_file_label.config(text=f"Selected File: {gui_m_to_a_marlea_file}")


a_to_m_in_buttons = ttk.Button(gui_root, text="Open File", command=open_file_dialog_in)
a_to_m_r_buttons = ttk.Button(gui_root, text="Open File", command=open_file_dialog_r)
a_to_m_out_entry = ttk.Entry(gui_root, textvariable=gui_a_to_m_marlea_file)

m_to_a_buttons = ttk.Button(gui_root, text="Open File", command=open_file_dialog_csv)
m_to_a_in_out_entry = ttk.Entry(gui_root, textvariable=gui_m_to_a_aleae_file_in)
m_to_a_r_out_entry = ttk.Entry(gui_root, textvariable=gui_m_to_a_aleae_file_r)


def aleae_to_marlea_btns():
    """Setup and change buttons when a-to-m mode is set."""
    selected_marlea_file_label.grid_remove()
    m_to_a_buttons.grid_remove()
    m_to_a_r_out_entry.grid_remove()
    m_to_a_in_out_entry.grid_remove()

    input_label.grid(column=1, row=5, sticky=tkinter.S)
    selected_in_file_label.grid(column=1, row=6, sticky=tkinter.W)
    selected_r_file_label.grid(column=1, row=7, sticky=tkinter.W)
    output_label.grid(column=1, row=8, sticky=tkinter.S)

    a_to_m_in_buttons.grid(column=0, row=6, sticky=tkinter.E)
    a_to_m_r_buttons.grid(column=0, row=7, sticky=tkinter.E)
    a_to_m_out_entry.grid(column=1, row=9, sticky=tkinter.NW)


def marlea_to_aleae_btns():
    """Setup and change buttons when m-to-a mode is set."""
    a_to_m_in_buttons.grid_remove()
    a_to_m_r_buttons.grid_remove()
    a_to_m_out_entry.grid_remove()
    selected_in_file_label.grid_remove()
    selected_r_file_label.grid_remove()

    input_label.grid(column=1, row=5, sticky=tkinter.S)
    selected_marlea_file_label.grid(column=1, row=6, sticky=tkinter.W)
    output_label.grid(column=1, row=7, sticky=tkinter.S)

    m_to_a_buttons.grid(column=0, row=6, sticky=tkinter.E)
    m_to_a_in_out_entry.grid(column=1, row=8, sticky=tkinter.NW)
    m_to_a_r_out_entry.grid(column=1, row=9, sticky=tkinter.NW)


# Set up the buttons and checkboxes for the gui
a_to_m_check = ttk.Radiobutton(mainframe, text='Aleae to MARlea', variable=gui_input_mode, value='a-to-m', command=aleae_to_marlea_btns)
m_to_a_check = ttk.Radiobutton(mainframe, text='MARlea to Aleae', variable=gui_input_mode, value='m-to-a', command=marlea_to_aleae_btns)
a_to_m_check.grid(column=0, row=0, sticky=tkinter.NW)
m_to_a_check.grid(column=1, row=0, sticky=tkinter.NW)

error_check_widget = ttk.Checkbutton(mainframe, text="Enable error checking", variable=gui_error_check_enable, onvalue=True, offvalue=False)
pipeline_widget = ttk.Checkbutton(mainframe, text="Enable pipelined execution", variable=gui_pipeline_enable, onvalue=True, offvalue=False)
waste_entry = ttk.Entry(gui_root, textvariable=gui_waste)
error_check_widget.grid(column=0, row=3, sticky=tkinter.NW)
pipeline_widget.grid(column=0, row=4, sticky=tkinter.NW)

waste_entry.grid(column=2, row=1, sticky=tkinter.NW)
waste_label.grid(column=1, row=1, sticky=tkinter.E)
aether_entry = ttk.Entry(gui_root, textvariable=gui_aether)
aether_label.grid(column=1, row=2, sticky=tkinter.E)
aether_entry.grid(column=2, row=2, sticky=tkinter.NW)


def gui_start_conversion():
    """The entry point for gui execution. """
    if not gui_error_check_enable.get():
       messagebox.askyesno(message='Error checking was not enabled. Any errors in your input files will cause unintended results.\nProceed with error checking enabled?',
        icon = 'warning',
        title = 'Warning', )

    if gui_input_mode.get() == "a-to-m":
        global gui_a_to_m_aleae_file_in
        global gui_a_to_m_aleae_file_r
        print("get")
        if gui_error_check_enable.get():
            check_aleae_files(gui_a_to_m_aleae_file_in, gui_a_to_m_aleae_file_r)
        print(gui_a_to_m_aleae_file_in, gui_a_to_m_aleae_file_r)

        if gui_a_to_m_aleae_file_in == "" or gui_a_to_m_aleae_file_r == "" or gui_a_to_m_marlea_file.get() == "":
            messagebox.showerror(title="Missing files", message="All files need to be entered.")
            return
        start_a_to_m_conversion(gui_a_to_m_aleae_file_in, gui_a_to_m_aleae_file_r, gui_a_to_m_marlea_file.get(),
                                gui_waste.get(), gui_aether.get(), gui_pipeline_enable.get())
    elif gui_input_mode.get() == "m-to-a":
        global gui_m_to_a_marlea_file
        if gui_error_check_enable.get():
            check_aleae_files(gui_m_to_a_aleae_file_in.get(), gui_m_to_a_aleae_file_r.get())

        if gui_m_to_a_marlea_file == "" or gui_m_to_a_aleae_file_in.get() == "" or gui_m_to_a_aleae_file_r.get() == "":
            messagebox.showerror(title="Missing files", message="All files need to be entered.")
            return
        start_m_to_a_conversion(gui_m_to_a_aleae_file_in.get(), gui_m_to_a_aleae_file_r.get(), gui_a_to_m_marlea_file,
                                gui_waste.get(), gui_aether.get(), gui_pipeline_enable.get())
    messagebox.showinfo(title="Conversion Complete", message="Input files have been converted.")
    exit(0)


confirm_btn = ttk.Button(gui_root, text="Start Conversion", command=gui_start_conversion)
confirm_btn.grid(column=1, row=10)


def open_file_read(filename):
    """The function attempts to open an input file for reading."""
    if os.path.isfile(filename):
        try:
            return open(filename, "r", newline='')
        except OSError:
            print("Input file " + filename + " has invalid file type")
    return None


def open_file_write(filename):
    """The function attempts to open an Aleae or MARlea input file for writing."""
    if os.path.isfile(filename):
        try:
            return open(filename, "w", newline='')
        except OSError:
            print("Input file " + filename + " failed to be opened.")
    else:
        try:
            return open(filename, "x", newline='')
        except OSError:
            print("Input file " + filename + " failed to be opened.")
    return None


def remove_empty_str_elems(lst):
    return [i for i in lst if i != ""]


def check_aleae_in_line(in_line):
    """
    Checks whether a line is a valid initialization statement within an Aleae .in file
    :param in_line: a list containing the elements of an Aleae initialization statement
    :return: True if line is valid or False if it detects an error
    """
    threshold_sym = {"LE", "LT", "GE", "GT", "N"}
    if len(in_line) >= 4:
        print(".in line not three elements: ", in_line)
        return False
    elif in_line[0].strip().isnumeric():
        print("Chem can't be a number: ", in_line)
        return False
    elif not in_line[1].strip().isnumeric():
        print("Amount must be an integer:", in_line)
        return False
    elif in_line[2] not in threshold_sym:
        print("Invalid threshold: ", in_line)
        return False
    elif len(in_line) > 3:
        if in_line[2] == "N":
            print("Threshold values not allowed for symbol 'N': ", in_line)
            return False
        elif in_line[2] in threshold_sym and not in_line[3].strip().isnumeric():
            print("Invalid threshold value: ", in_line)
            return False
    return True


def check_aleae_r_line(r_line, chems):
    """
    Checks whether a line is a valid reaction statement within an Aleae .r file
    :param r_line: a list containing the elements of an Aleae initialization statement
    :param chems: a set containing all chemicals that are found in the .in file
    :return: True if line is valid or False if it detects an error
    """
    if len(r_line) != 3:
        print("Aleae reactions need three fields: ", r_line)
        return False
    if not r_line[2].strip().isnumeric():
        print("Rate must be a number: ", r_line[2].strip())
        return False

    for i in range(2):
        temp_field = r_line[i].strip().split()
        if len(temp_field) % 2 == 1:
            print("Invalid reaction format: ", r_line)
            return False
        for j in range(0, len(temp_field), 2):
            if temp_field[j].strip().isnumeric() or not temp_field[j + 1].strip().isnumeric():
                print("invalid term: " + temp_field[j] + " " + temp_field[j + 1])
                return False
            elif temp_field[j].strip() not in chems:
                print("Chem in Aleae reaction is not initialized: ", temp_field[j])
                return False
    return True


def check_aleae_files(aleae_in_filename, aleae_r_filename):
    """
    Checks whether all line in both Aleae files are valid
    :param aleae_in_filename: name of Aleae .in file
    :param aleae_r_filename: name of Aleae .r file
    :return: True if both files contains valid lines or False if it detects an error in either file
    """
    f_init = open_file_read(aleae_in_filename)
    if f_init is None:
        print(".in file failed to be opened.")
        return False

    line_counter = 1
    chems = set()                                           # Tracks all discovered chems
    temp = f_init.readline()
    while temp != "":
        temp_line = temp.strip().split()
        if len(temp_line) < 1:                              # Skip empty lines
            temp = f_init.readline()
            line_counter += 1
            continue
        if not check_aleae_in_line(temp_line):
            f_init.close()
            print("Syntax error at line", line_counter, "in", aleae_in_filename + ": ", temp.strip('\n'))
            return False

        line_counter += 1
        chems.add(temp_line[0])                             # Found a chemical
        temp = f_init.readline()
    f_init.close()

    f_react = open_file_read(aleae_r_filename)
    if f_react is None:
        print(".r file failed to be opened.")
        return False

    line_counter = 1
    temp = f_react.readline()
    while temp != "":
        temp_line = temp.strip().split(ALEAE_FIELD_SEPARATOR)
        if len(temp_line) < 1:                                  # Skip empty lines
            temp = f_react.readline()
            line_counter += 1
            continue
        elif not check_aleae_r_line(temp_line, chems):
            f_react.close()
            print("Syntax error at line", line_counter, "in", aleae_r_filename + ": ", temp.strip('\n'))
            return False
        line_counter += 1
        temp = f_react.readline()
    f_react.close()

    return True


def check_marlea_init(row_in):
    """
    Checks whether a row is a valid initialization statement within a MARlea file
    :param row_in: a list containing the elements of an MARlea initialization statement
    :return: True if line is valid or False if it detects an error
    """
    if "+" in row_in[0].strip() or " " in row_in[0].strip():
        print("Invalid use of a term separator")
        return False
    elif (not row_in[0].strip().isnumeric() and row_in[1].strip().isnumeric()
          and row_in[0].strip() != MARLEA_NULL):
        if row_in[1].strip() == "0":
            print("MARlea chemicals cannot be initialized to zero")
            return False
        return True
    print("Initialization statement does not follow MARlea's format")
    return False


def check_marlea_reaction(row_r):
    """
    Checks whether a row is a valid reaction statement within a MARlea file
    :param row_r: a list containing the elements of an MARlea reaction statement
    :return: True if line is valid or False if it detects an error
    """
    terms = ["", ""]
    if MARLEA_ARROW in row_r[0]:
        reaction = row_r[0].strip().split(MARLEA_ARROW)

        if len(reaction) == 2:
            terms[0] = reaction[0].strip().split(MARLEA_TERM_SEPARATOR)     # Get reactant terms
            terms[1] = reaction[1].strip().split(MARLEA_TERM_SEPARATOR)     # Get product terms
        else:
            print("Reactants and products must be separated by '=>'")
            return False

        if len(terms[0]) > 1 and "NULL" in set(terms[0]):
            print("Improper use of the NULL keyword in reaction statement")
            return False
        elif len(terms[1]) > 1 and "NULL" in set(terms[1]):
            print("Improper use of the NULL keyword in reaction statement")
            return False
    else:
        return False

    for i in range(2):
        for elem in terms[i]:
            tmp = elem.strip().split()
            if len(tmp) < 1:                                    # Result of a trailing/leading '+' symbol in a reaction
                print("Misuse of a term separator")
                return False
            elif len(terms[i]) > 1 and MARLEA_NULL in tmp[0]:
                print("Improper use of the NULL keyword in MARlea reaction statement")
                return False
            elif len(tmp) < 2 and tmp[0].strip().isnumeric():
                print("Coefficients cannot be in a term without a chemical")
                return False
            elif len(tmp) == 2:
                if tmp[1].strip().isnumeric() or not tmp[0].strip().isnumeric():
                    print("Coefficients cannot be in a term without a chemical")
                    return False
                elif "NULL" in tmp[1].strip() or MARLEA_NULL in tmp[0].strip():
                    print("NULL keywords can only be in either the reactant or product side")
                    return False
                elif tmp[0] == '1':
                    print("Explicit coefficients in MARlea cannot be one")
                    return False
            elif len(tmp) > 2:
                print("Terms can only contain a chemical and its coefficient")
                return False
    return True


def check_marlea_row(row):
    """
    Checks whether a line is a valid initialization statement within an Aleae .in file
    :param row: a list containing the elements of an MARlea row
    :return: True if line is valid or False if it detects an error
    """
    if row[0] == "" and row[1] == "":
        return True
    elif "//" in row[1]:                                    # Skip comments unless they're invalid
        if row[0] != "":
            return False
        return True
    elif "//" in row[0]:
        if row[1] != "":
            return False
        return True
    elif not row[1].strip().isnumeric():
        return False
    elif MARLEA_ARROW in row[0]:                            # Detect reaction statement and check
        return check_marlea_reaction(row)
    elif MARLEA_TERM_SEPARATOR in row[0]:
        return False
    else:
        return check_marlea_init(row)                       # No reaction statement detected, so it must be an init statement


def check_marlea_file(MARlea_input_filename):
    """
    Checks whether all line in a MARlea files are valid
    :param aleae_in_filename: name of Aleae .in file
    :return: True if the file contains valid rows or False if it detects an error in the file
    """
    f_MARlea_input = open_file_read(MARlea_input_filename)
    if f_MARlea_input is None:
        print("MARlea file failed to be opened.")
        return False

    line_counter = 1
    reader = csv.reader(f_MARlea_input, "excel")
    for row in reader:
        if len(row) < 1:                                    # Skip empty lines
            line_counter += 1
            continue
        elif not check_marlea_row(row):
            f_MARlea_input.close()
            print("Syntax error at line", line_counter, "in", MARlea_input_filename + ":", row)
            return False
        line_counter += 1
    f_MARlea_input.close()
    return True


def read_aleae_in_file(aleae_in_filename, aether):
    """
    Read each line from an Aleae input file, pre-process it if needed, and send it to a writer via a queue
    :param aleae_in_filename: name of Aleae .in file
    :param aether: list of chemicals that will be converted to a NULL in the reactants
    """
    f_init = open_file_read(aleae_in_filename)
    if f_init is None:
        input_file_reader_to_converter_queue.put(END_PROCEDURE)
        input_file_reader_to_output_writer_queue.put(END_PROCEDURE)
        return

    temp = f_init.readline()
    while temp != "":                                                           # Convert .in file to beginning of MARlea file
        temp_row = temp.split(" ")
        if temp_row[1] != "0" and temp_row[0] not in set(aether):
            input_file_reader_to_output_writer_queue.put(temp_row[:2])
        temp = f_init.readline()

    f_init.close()

    input_file_reader_to_output_writer_queue.put([])
    input_file_reader_to_output_writer_queue.put(END_PROCEDURE)


def read_aleae_r_file(aleae_r_filename):
    """
    Read each line from an Aleae .r input file and send it to a converter via a queue
    :param aleae_r_filename: name of Aleae .r file
    """
    f_react = open_file_read(aleae_r_filename)
    if f_react is None:
        input_file_reader_to_converter_queue.put(END_PROCEDURE)
        input_file_reader_to_output_writer_queue.put(END_PROCEDURE)
        return

    temp = f_react.readline()
    while temp != "":                                                           # Convert .r file to reaction in a MARlea file
        input_file_reader_to_converter_queue.put(temp)
        temp = f_react.readline()

    input_file_reader_to_converter_queue.put(END_PROCEDURE)
    f_react.close()


def aleae_to_marlea_converter(waste, aether):
    """
    Converts each line from Aleae file into a line from a MARlea file.
    :param waste: a specified chemical that will be converted to a NULL in the products
    :param aether: list of chemicals that will be converted to a NULL in the reactants
    """
    temp = input_file_reader_to_converter_queue.get()
    while temp != END_PROCEDURE:
        converted_reaction = []
        temp_row = temp.split(ALEAE_FIELD_SEPARATOR)                            # Split reactants, products, and rates into elements of list called temp_row

        converted_reaction_str = ""
        for i in range(ReactionParts.NUM_FIELDS.value):
            chem_reaction = remove_empty_str_elems(temp_row[i].split(" "))      # Split reactants/products and their coefficients into elements of chem_reactiosn
            if len(chem_reaction) > 1:
                for j in range(0, len(chem_reaction), 2):
                    (chem_reaction[j], chem_reaction[j + 1]) = (chem_reaction[j + 1], chem_reaction[j])

            if i == ReactionParts.REACTION_RATE.value:                          # Strip and add rate to converted reactions
                chem_rate = chem_reaction[0].strip()
                converted_reaction.append(converted_reaction_str.strip())
                converted_reaction.append(" " + chem_rate)
            else:
                for k in range(len(chem_reaction)):                             # Convert reactant/product part of the reaction to MARlea
                    if ((i == ReactionParts.REACTANTS.value and chem_reaction[k] in set(aether)) or
                            (i == ReactionParts.PRODUCTS.value and chem_reaction[k] == waste)):
                        chem_reaction[k] = MARLEA_NULL
                        converted_reaction_str += chem_reaction[k] + " "
                    elif not chem_reaction[k] in set(aether):
                        if chem_reaction[k] != "1":
                            converted_reaction_str += chem_reaction[k] + " "
                        if chem_reaction[k] == waste:
                            chem_reaction[k] = MARLEA_NULL
                            converted_reaction_str += chem_reaction[k] + " "
                        if not chem_reaction[k].isnumeric() and k < len(chem_reaction) - 1:
                            converted_reaction_str += MARLEA_TERM_SEPARATOR + " "
                if i == ReactionParts.REACTANTS.value:
                    converted_reaction_str += MARLEA_ARROW + ' '

        converter_to_output_file_writer_queue_0.put(converted_reaction)
        temp = input_file_reader_to_converter_queue.get()

    converter_to_output_file_writer_queue_0.put(END_PROCEDURE)


def write_marlea_file(MARlea_output_filename):
    """
    Receive any line from the Aleae input file reader and converter and write to the MARlea file.
    :param MARlea_output_filename: name of MARlea file
    """
    f_MARlea_output = open_file_write(MARlea_output_filename)
    if f_MARlea_output is None:
        return

    writer = csv.writer(f_MARlea_output, "excel")
    temp = input_file_reader_to_output_writer_queue.get()
    while temp != END_PROCEDURE:
        writer.writerow(temp)                                               # Write line from any reader
        temp = input_file_reader_to_output_writer_queue.get()

    temp = converter_to_output_file_writer_queue_0.get()
    while temp != END_PROCEDURE:
        writer.writerow(temp)                                               # Write processes line from converter
        temp = converter_to_output_file_writer_queue_0.get()

    f_MARlea_output.close()


def read_marlea_file(MARlea_input_filename):
    """
    Read each row from a MARlea input file, pre-process said row, and send it to either a converter or writer.
    :param MARlea_input_filename: name of MARlea file as input
    """
    f_MARlea_input = open_file_read(MARlea_input_filename)
    if f_MARlea_input is None:
        input_file_reader_to_converter_auxilliary_queue.put(END_PROCEDURE)
        input_file_reader_to_converter_queue.put(END_PROCEDURE)
        input_file_reader_to_output_writer_queue.put(END_PROCEDURE)
        return
    reader = csv.reader(f_MARlea_input, "excel")

    for row in reader:
        if len(row) > 0 and "//" not in row[1] and "//" not in row[0]:       # Filter out row without initialized chemicals or reactions
            if MARLEA_ARROW in row[0]:
                input_file_reader_to_converter_queue.put(row)                # Send any reactions to the converter
            elif row[1] != "" and row[0] != "":
                input_file_reader_to_output_writer_queue.put(row[0].strip() + " " + row[1].strip() + ' N\n')
                input_file_reader_to_converter_auxilliary_queue.put(row)

    input_file_reader_to_converter_auxilliary_queue.put(END_PROCEDURE)
    input_file_reader_to_output_writer_queue.put(END_PROCEDURE)
    input_file_reader_to_converter_queue.put(END_PROCEDURE)

def marlea_to_aleae_converter(waste, aether):
    """
    Convert a row from the reader into a line for either an Aleae .in file or an Aleae .r file and send it to the
    appropriate writer.
    :param waste: a specified chemical that will be converted to a NULL in the products
    :param aether: list of chemicals that will be converted to a NULL in the reactants
    """
    found_chems = dict()

    temp = input_file_reader_to_converter_auxilliary_queue.get()                        # .in output will be incorrect if known chemicals are not found before processing reactions
    while temp != END_PROCEDURE:
        found_chems[temp[0]] = temp[1]
        temp = input_file_reader_to_converter_auxilliary_queue.get()

    temp = input_file_reader_to_converter_queue.get()
    while temp != END_PROCEDURE:
        chem_reaction_str = ""
        temp_rate = temp[1].strip()
        temp_reaction_pieces = temp[0].split(MARLEA_ARROW)                              # Split reactions into reactants and products

        aether_loc_found = False
        for j in range(ReactionParts.NUM_FIELDS.value - 1):                             # MARlea only contains two relevant fields: reaction and rate
            temp_reaction_terms = temp_reaction_pieces[j].strip().split(MARLEA_TERM_SEPARATOR)  # Split reactants/products into terns
            for k in range(len(temp_reaction_terms)):
                temp_term = temp_reaction_terms[k].strip().split(" ")

                if temp_term[0] == MARLEA_NULL:                                         # Add aether or waste term depending on location of detected NULL
                    if j == ReactionParts.REACTANTS.value:
                        temp_term[0] = aether[0]
                        aether_loc_found = True
                    elif j == ReactionParts.PRODUCTS.value:
                        temp_term[0] = waste
                elif aether_loc_found and j == ReactionParts.PRODUCTS.value:
                    chem_reaction_str += aether[0] + ' 1 '                              # Add aether term to reaction string

                if len(temp_term) > 1:
                    (temp_term[0], temp_term[1]) = (temp_term[1], temp_term[0])
                    chem_reaction_str += temp_term[0] + " " + temp_term[1]
                else:
                    temp_term.append("1")                                               # Add '1' as coefficient if terms lacks one
                    chem_reaction_str += temp_term[0] + ' 1'

                if temp_term[0] not in set(found_chems.keys()):
                    if len(aether) > 0 and temp_term[0] == aether[0]:             # Add discovered chemical to found_chems
                        found_chems[temp_term[0]] = '1'
                    else:
                        found_chems[temp_term[0]] = '0'
                    converter_to_output_file_writer_queue_0.put(temp_term[0].strip() + " " +
                                                                found_chems[temp_term[0]].strip() + ' N\n')
                chem_reaction_str += " "
            if j == ReactionParts.REACTANTS.value:
                chem_reaction_str += ALEAE_FIELD_SEPARATOR + " "

        chem_reaction_str = chem_reaction_str.strip()
        converter_to_output_file_writer_queue_1.put(chem_reaction_str + ' ' + ALEAE_FIELD_SEPARATOR
                                                    + ' ' + temp_rate + '\n')

        temp = input_file_reader_to_converter_queue.get()

    converter_to_output_file_writer_queue_0.put(END_PROCEDURE)
    converter_to_output_file_writer_queue_1.put(END_PROCEDURE)

def write_aleae_in_file(aleae_in_filename):
    """
    Receive row from either the reader or converter and write to .in Aleae file
    :param aleae_in_filename: name of Aleae .in file as output
    """
    f_aleae_output_in = open_file_write(aleae_in_filename)
    if f_aleae_output_in is None:
        return

    temp = input_file_reader_to_output_writer_queue.get()
    while temp != END_PROCEDURE:
        f_aleae_output_in.write(temp)
        temp = input_file_reader_to_output_writer_queue.get()                       # Write line from reader

    temp = converter_to_output_file_writer_queue_0.get()
    while temp != END_PROCEDURE:
        f_aleae_output_in.write(temp)                                               # Write lines from converter
        temp = converter_to_output_file_writer_queue_0.get()

    f_aleae_output_in.close()


def write_aleae_r_file(aleae_r_filename):
    """
    Receive row from either the converter and write to .r Aleae file
    :param aleae_r_filename:
    :return:
    """
    f_aleae_output_r = open_file_write(aleae_r_filename)
    if f_aleae_output_r is None:
        return

    temp = converter_to_output_file_writer_queue_1.get()
    while temp != END_PROCEDURE:
        f_aleae_output_r.write(temp)                                                # Write converted line
        temp = converter_to_output_file_writer_queue_1.get()

    f_aleae_output_r.close()


def run_error_checking(aleae_in_file, aleae_r_file, marlea_file ):
    print("Beginning file checking.")
    if not os.path.isfile("error_checker.py"):
        print("Error checker script not found. Is it named 'error_checker.py' "
              + "and in the same directory as converter.py?")
        return False
    elif aleae_in_file is not None and aleae_r_file is not None:
        return check_aleae_files(aleae_in_file, aleae_r_file)
    elif marlea_file is not None:
        return check_marlea_file(marlea_file)
    exit(0)


def start_a_to_m_conversion(aleae_in_filename, aleae_r_filename, marlea_filename, waste, aether, pipeline_enabled):
    if pipeline_enabled:
        reader_in_thread = Thread(None, read_aleae_in_file, None, [aleae_in_filename, aether, ])
        reader_r_thread = Thread(None, read_aleae_r_file, None, [aleae_r_filename, ])
        converter_thread = Thread(None, aleae_to_marlea_converter, None, [waste, aether, ])
        writer_thread = Thread(None, write_marlea_file, None, [marlea_filename, ])

        reader_in_thread.start()
        reader_r_thread.start()
        converter_thread.start()
        writer_thread.start()

        reader_in_thread.join()
        reader_r_thread.join()
        converter_thread.join()
        writer_thread.join()
    else:
        read_aleae_in_file(aleae_in_filename, aether)
        read_aleae_r_file(aleae_r_filename)
        aleae_to_marlea_converter(waste, aether)
        write_marlea_file(marlea_filename)


def start_m_to_a_conversion(aleae_in_filename, aleae_r_filename, marlea_filename, waste, aether, pipeline_enabled):
    if pipeline_enabled:
        reader_thread = Thread(None, read_marlea_file, None, [marlea_filename, ])
        converter_thread = Thread(None, marlea_to_aleae_converter, None, [waste, aether, ])
        writer_thread_in = Thread(None, write_aleae_in_file, None, [aleae_in_filename, ])
        writer_thread_r = Thread(None, write_aleae_r_file, None, [aleae_r_filename, ])

        reader_thread.start()
        converter_thread.start()
        writer_thread_in.start()
        writer_thread_r.start()

        reader_thread.join()
        converter_thread.join()
        writer_thread_in.join()
        writer_thread_r.join()
    else:
        read_marlea_file(marlea_filename)
        marlea_to_aleae_converter(waste, aether)
        write_aleae_in_file(aleae_in_filename)
        write_aleae_r_file(aleae_r_filename)

def scan_args():
    """
    The function interprets the command-line input and parses it for any information needed to start converting input
    files. All error correction is handled in this function.
    """

    waste_local = ""
    aether_local = []

    if sys.version_info.major < 3 and sys.version_info.minor < 8:
        print("Version of Python must be 3.8 or higher")
        exit(0)

    # All the commands and their associated flags
    main_parser = argparse.ArgumentParser(prog="converter.py", add_help=True)
    subparsers = main_parser.add_subparsers(dest="command")

    a_to_m_parser = subparsers.add_parser("a-to-m", usage="Convert Aleae files into MARlea files", help="Convert Aleae files to an MARlea equivalent")
    a_to_m_parser.add_argument("-i", "--input", action='store', nargs=2, required=True, help="Paths to the .in and .r Aleae files")
    a_to_m_parser.add_argument("-p", "--pipeline_enable", action='store_true', help="Enable pipelined Execution of file conversion")
    a_to_m_parser.add_argument("-e", "--error_check_enable", action='store_true', help="Enable pre-conversion error checking of Aleae Files")
    a_to_m_parser.add_argument("-o", "--output", action='store', required=True, help="Path to new or preexisting MARlea file")
    a_to_m_parser.add_argument("--waste", action='store', required=False, help="A chemical that is the waste products of reactions")
    a_to_m_parser.add_argument("--aether", action='store', nargs='*', help="A list of chemicals that enable continous production of other chemicals")

    m_to_a_parser = subparsers.add_parser("m-to-a", usage="Convert MARlea files into Aleae files", help="Convert MARlea file to Aleae equivalents")
    m_to_a_parser.add_argument("-i", "--input", action='store', required=True, help="Paths to .csv MARlea file")
    m_to_a_parser.add_argument("-p", "--pipeline_enable", action='store_true', help="Enable pipelined Execution of file conversion")
    m_to_a_parser.add_argument("-e", "--error_check_enable", action='store_true', help="Enable pre-conversion error checking of Aleae Files")
    m_to_a_parser.add_argument("-o", "--output", action='store', nargs=2, required=True, help="Paths to new or preexisting .in and .r Aleae files")
    m_to_a_parser.add_argument("--waste", action='store', required=False, help="A chemical that is the waste products of reactions")
    m_to_a_parser.add_argument("--aether", action='store', nargs='*', help="A list of chemicals that enable continous production of other chemicals")

    gui_parser = subparsers.add_parser("gui", usage="summons the gui", help="Summon the program's graphical user interface")
    gui_parser.add_argument("-v", "--verbose", action='store_true')

    parsed_args = main_parser.parse_args(sys.argv[1:])  # Extract some of the arguments from the command-line input
    input_mode = parsed_args.command

    if input_mode is None:
        print("No commands entered. Closing Program.")
        exit(0)

    if input_mode == "gui":
        gui_root.mainloop()
        exit(0)
    else:
        error_check_enable = parsed_args.error_check_enable

        if not error_check_enable:
            proceed = input("Error checking was not enabled. Any errors in your input files will cause unintended results.\n "
                            + "Proceed with error checking enabled? (Y/n): ")
            while proceed.strip().lower() != "y" and proceed.strip().lower() != "n":
                proceed = input("Invalid input: Proceed with error checking enabled? (Y/n): ")
                if proceed.strip().lower() == "y":
                    error_check_enable = True
                elif proceed.strip().lower() != "n":
                    print("Invalid keyboard input.")

            if proceed.strip().lower() == "y":
                error_check_enable = True


        if parsed_args.waste is not None:
            waste_local = parsed_args.waste

        if parsed_args.aether is not None:
            aether_local = parsed_args.aether
            for elem in aether_local:
                if elem == waste_local:
                    print("Error: Aether chemical", elem, "is the same as", waste_local)
                    exit(0)

        input_files = parsed_args.input                             # Extract the rest of the command-line input
        pipeline_enabled = parsed_args.pipeline_enable
        output_files = parsed_args.output

    if input_mode == "a-to-m":
        if ".in" in input_files[0] and ".r" in input_files[1]:
            aleae_in_filename = input_files[0]
            aleae_r_filename = input_files[1]
        elif ".in" in input_files[1] and ".r" in input_files[0]:
            aleae_in_filename = input_files[1]
            aleae_r_filename = input_files[0]
        else:
            print("Error: Invalid input file type")
            exit(-1)

        marlea_filename = output_files
        if ".csv" not in marlea_filename:
            print("Error: Invalid output file type")
            exit(-1)

        if error_check_enable:
            if not check_aleae_files(aleae_in_filename, aleae_r_filename):
                exit(0)
            print("No errors were found. Beginning file conversion.")

        start_a_to_m_conversion(aleae_in_filename, aleae_r_filename, marlea_filename, waste_local, aether_local,
                         pipeline_enabled)
    elif input_mode == "m-to-a":
        if ".in" in output_files[0] or ".r" in output_files[1]:
            aleae_in_filename = output_files[0]
            aleae_r_filename = output_files[1]
        elif ".in" in output_files[1] or ".r" in output_files[0]:
            aleae_in_filename = output_files[1]
            aleae_r_filename = output_files[0]
        else:
            print("Error: Invalid output file type")
            exit(-1)

        marlea_filename = input_files
        if ".csv" not in marlea_filename:
            print("Error: Invalid input file type")
            exit(-1)

        if error_check_enable:
            if not check_marlea_file(marlea_filename):
                exit(0)
            print("No errors were found. Beginning file conversion.")

        start_m_to_a_conversion(aleae_in_filename, aleae_r_filename, marlea_filename, waste_local, aether_local,
                         pipeline_enabled)
    elif input_mode == "gui":
        print("fds")
    else:
        print("Error: Invalid command.")
        exit(-1)


scan_args()
