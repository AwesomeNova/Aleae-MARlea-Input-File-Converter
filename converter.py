"""
Name: AwesomeNova
Updated at: 10/18/2024

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
import re
from enum import IntEnum, StrEnum
from threading import Thread
from tkinter import Tk, ttk, StringVar, BooleanVar, filedialog, messagebox

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


gui_root = Tk()                                                        # Set up the gui
gui_root.title("Aleae-MARlea File Converter")
gui_root.minsize(500, 300)
button_frame = ttk.Frame(gui_root, padding="8 8 12 12")
file_frame = ttk.Frame(gui_root, padding="8 8 12 12")
waste_aether_frame = ttk.Frame(gui_root, padding="8 8 12 12")
conversion_button_frame = ttk.Frame(gui_root, padding="8 8 12 12")
button_frame.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
file_frame.grid(column=1, row=0)
waste_aether_frame.grid(column=0, row=1)
conversion_button_frame.grid(column= 1, row=1)
gui_root.columnconfigure(0, weight=1)
gui_root.columnconfigure(1, weight=1)
gui_root.columnconfigure(2, weight=1)
gui_root.rowconfigure(list(range(10)), weight=1)

radio_button_label = ttk.Label(button_frame, text="Conversion mode select:")
radio_button_label.grid(column=0, row=0, sticky=tkinter.W)
flag_label = ttk.Label(button_frame, text="Select enable flags:")
flag_label.grid(column=0, row=4, sticky=tkinter.W)

input_label = ttk.Label(file_frame, text="Input Files")
output_label = ttk.Label(file_frame, text="Output Files")
selected_input_in_file_label = ttk.Label(file_frame, text="Selected File:")
selected_input_r_file_label = ttk.Label(file_frame, text="Selected File:")
selected_input_marlea_file_label = ttk.Label(file_frame, text="Selected File:")
selected_output_in_file_label = ttk.Label(file_frame, text="Selected File:")
selected_output_r_file_label = ttk.Label(file_frame, text="Selected File:")
selected_output_marlea_file_label = ttk.Label(file_frame, text="Selected File:")

waste_aether_label = ttk.Label(waste_aether_frame, text="Enter waste and aether chemicals \n(Separate aether chemicals by whitespace)")
waste_label = ttk.Label(waste_aether_frame, text="Waste:")
aether_label = ttk.Label(waste_aether_frame, text="Aether:")

gui_input_mode = StringVar()

gui_a_to_m_aleae_file_in = ""                                           # Initialize gui file variables
gui_a_to_m_aleae_file_r = ""
gui_a_to_m_marlea_file = ""

gui_m_to_a_marlea_file = ""
gui_m_to_a_aleae_file_in = ""
gui_m_to_a_aleae_file_r = ""

gui_pipeline_enable=BooleanVar()

gui_waste=StringVar()
gui_aether=StringVar()


def open_file_dialog_in():
    """Prompt the user with an open file dialog and set the .in file variable to user input."""
    global gui_a_to_m_aleae_file_in
    gui_a_to_m_aleae_file_in = filedialog.askopenfilename(title="Select a File", filetypes=[("Aleae initialization files", "*.in")])
    if gui_a_to_m_aleae_file_in:
        selected_input_in_file_label.config(text=f"Selected File: {gui_a_to_m_aleae_file_in}")

def open_file_dialog_r():
    """Prompt the user with an open file dialog and set the .r file variable to user input."""
    global gui_a_to_m_aleae_file_r
    gui_a_to_m_aleae_file_r = filedialog.askopenfilename(title="Select a File", filetypes=[("Aleae reaction files", "*.r")])
    if gui_a_to_m_aleae_file_r:
        selected_input_r_file_label.config(text=f"Selected File: {gui_a_to_m_aleae_file_r}")

def open_file_dialog_csv():
    """Prompt the user with a open file dialog and set the .csv file variable to user input."""
    global gui_m_to_a_marlea_file
    gui_m_to_a_marlea_file = filedialog.askopenfilename(title="Select a File", filetypes=[("MARlea files", "*.csv")])
    if gui_m_to_a_marlea_file:
        selected_input_marlea_file_label.config(text=f"Selected File: {gui_m_to_a_marlea_file}")


def save_file_dialog_in():
    """Prompt the user with a save file dialog and set the .in file variable for output."""
    global gui_m_to_a_aleae_file_in
    gui_m_to_a_aleae_file_in = filedialog.asksaveasfilename(title="Select a File", filetypes=[("Aleae initialization files", "*.in")])
    if gui_m_to_a_aleae_file_in:
        selected_output_in_file_label.config(text=f"Selected File: {gui_m_to_a_aleae_file_in}")

def save_file_dialog_r():
    """Prompt the user with an save file dialog and set the .r file variable for output."""
    global gui_m_to_a_aleae_file_r
    gui_m_to_a_aleae_file_r = filedialog.asksaveasfilename(title="Select a File", filetypes=[("Aleae reaction files", "*.r")])
    if gui_m_to_a_aleae_file_r:
        selected_output_r_file_label.config(text=f"Selected File: {gui_m_to_a_aleae_file_r}")

def save_file_dialog_csv():
    """Prompt the user with a save file dialog and set the .csv file variable for output."""
    global gui_a_to_m_marlea_file
    gui_a_to_m_marlea_file = filedialog.asksaveasfilename(title="Select a File", filetypes=[("MARlea files", "*.csv")])
    if gui_a_to_m_marlea_file:
        selected_output_marlea_file_label.config(text=f"Selected File: {gui_a_to_m_marlea_file}")


a_to_m_in_buttons = ttk.Button(file_frame, text="Open File", command=open_file_dialog_in)
a_to_m_r_buttons = ttk.Button(file_frame, text="Open File", command=open_file_dialog_r)
a_to_m_out_btn = ttk.Button(file_frame, text="Create File", command=save_file_dialog_csv)

m_to_a_buttons = ttk.Button(file_frame, text="Open File", command=open_file_dialog_csv)
m_to_a_in_out_btn = ttk.Button(file_frame, text="Create File", command=save_file_dialog_in)
m_to_a_r_out_btn = ttk.Button(file_frame, text="Create File", command=save_file_dialog_r)


def aleae_to_marlea_btns():
    """Setup and change buttons when a-to-m mode is set."""
    selected_input_marlea_file_label.grid_remove()
    selected_output_in_file_label.grid_remove()
    selected_output_r_file_label.grid_remove()
    m_to_a_buttons.grid_remove()
    m_to_a_r_out_btn.grid_remove()
    m_to_a_in_out_btn.grid_remove()

    input_label.grid(column=1, row=0, sticky=tkinter.S)
    selected_input_in_file_label.grid(column=1, row=1, sticky=tkinter.W)
    selected_input_r_file_label.grid(column=1, row=2, sticky=tkinter.W)
    output_label.grid(column=1, row=3, sticky=tkinter.S)

    selected_output_marlea_file_label.grid(column=1, row=4, sticky=tkinter.W)
    a_to_m_in_buttons.grid(column=0, row=1, sticky=tkinter.E)
    a_to_m_r_buttons.grid(column=0, row=2, sticky=tkinter.E)
    a_to_m_out_btn.grid(column=0, row=4, sticky=tkinter.N)


def marlea_to_aleae_btns():
    """Setup and change buttons when m-to-a mode is set."""
    a_to_m_in_buttons.grid_remove()
    a_to_m_r_buttons.grid_remove()
    a_to_m_out_btn.grid_remove()
    selected_input_in_file_label.grid_remove()
    selected_input_r_file_label.grid_remove()
    selected_output_marlea_file_label.grid_remove()

    input_label.grid(column=1, row=0, sticky=tkinter.S)
    selected_input_marlea_file_label.grid(column=1, row=1, sticky=tkinter.W)
    output_label.grid(column=1, row=2, sticky=tkinter.S)

    selected_output_in_file_label.grid(column=1, row=3, sticky=tkinter.W)
    selected_output_r_file_label.grid(column=1, row=4, sticky=tkinter.W)
    m_to_a_buttons.grid(column=0, row=1, sticky=tkinter.E)
    m_to_a_in_out_btn.grid(column=0, row=3, sticky=tkinter.N)
    m_to_a_r_out_btn.grid(column=0, row=4, sticky=tkinter.N)


# Set up the buttons and checkboxes for the gui
a_to_m_check = ttk.Radiobutton(button_frame, text='Aleae to MARlea', variable=gui_input_mode, value='a-to-m', command=aleae_to_marlea_btns)
m_to_a_check = ttk.Radiobutton(button_frame, text='MARlea to Aleae', variable=gui_input_mode, value='m-to-a', command=marlea_to_aleae_btns)
a_to_m_check.grid(column=0, row=1, sticky=tkinter.SW)
m_to_a_check.grid(column=0, row=2, sticky=tkinter.SW)

pipeline_widget = ttk.Checkbutton(button_frame, text="Enable pipelined execution", variable=gui_pipeline_enable, onvalue=True, offvalue=False)
pipeline_widget.grid(column=0, row=6, sticky=tkinter.SW)

waste_aether_label.grid(column=2, row=0)
waste_entry = ttk.Entry(waste_aether_frame, textvariable=gui_waste)
waste_entry.grid(column=2, row=1, sticky=tkinter.NW)
waste_label.grid(column=1, row=1, sticky=tkinter.E)
aether_entry = ttk.Entry(waste_aether_frame, textvariable=gui_aether)
aether_label.grid(column=1, row=2, sticky=tkinter.E)
aether_entry.grid(column=2, row=2, sticky=tkinter.NW)


def gui_start_conversion():
    """The entry point for gui execution. """
    if gui_input_mode.get() == "":
        return

    if "," in gui_aether.get() or "//" in gui_aether.get():
        messagebox.showerror(title="Invalid aether terms", message="Please enter aether terms as instructed.")
        return
    elif len(gui_waste.get().split()) > 1 or "," in gui_waste.get() or "//" in gui_waste.get():
        messagebox.showerror(title="Invalid waste term", message="Please enter only one waste term. No commas or '//' strings.")
        return

    if gui_input_mode.get() == "a-to-m":
        global gui_a_to_m_aleae_file_in
        global gui_a_to_m_aleae_file_r


        if gui_a_to_m_aleae_file_in == "" or gui_a_to_m_aleae_file_r == "" or gui_a_to_m_marlea_file == "":
            messagebox.showerror(title="Missing files", message="All files need to be entered.")
            return
        else:
            start_a_to_m_conversion(gui_a_to_m_aleae_file_in, gui_a_to_m_aleae_file_r, gui_a_to_m_marlea_file,
                                    gui_waste.get(), gui_aether.get(), gui_pipeline_enable.get())
    elif gui_input_mode.get() == "m-to-a":
        global gui_m_to_a_marlea_file

        if gui_m_to_a_marlea_file == "" or gui_m_to_a_aleae_file_in == "" or gui_m_to_a_aleae_file_r == "":
            messagebox.showerror(title="Missing files", message="All files need to be entered.")
            return
        else:
            start_m_to_a_conversion(gui_m_to_a_aleae_file_in, gui_m_to_a_aleae_file_r, gui_m_to_a_marlea_file,
                                    gui_waste.get(), gui_aether.get(), gui_pipeline_enable.get())

    messagebox.showinfo(title="Conversion Complete", message="Input files have been converted.")


confirm_btn = ttk.Button(gui_root, text="Start Conversion", command=gui_start_conversion)
confirm_btn.grid(column=1, row=1)


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


class NodeEnum(StrEnum):
    EQUATION = "EQUATION"
    FIELD = "FIELD"
    RATE = "RATE"
    TERM = "TERM"
    COEFF = "COEFF"
    CHEM = "CHEM"
    FIELD_SEP = "FIELD_SEP"
    TERM_SEP = "TERM_SEP"
    MARLEA_NULL = "MARLEA_NULL"
    MARLEA_ARROW = "MARLEA_ARROW"


class AleaeMARLeaNode:
    def __init__(self, type, value, children):
        self.type = type
        self.value = value
        self.children = children


class Tokenizer:
    def __init__(self, line):
        self.line = line
        self.equ = self.line.strip().split()
        self.tokens = []
        self.cursor = 0

    def tokenize(self):
        pass

    def investigate(self, msg, token):
        print(msg, token, "from", self.line.strip())

    def check_token_at_cursor(self, offset):
        return self.tokens[self.cursor+offset]

    def get_cursor_pos(self):
        return self.cursor

    def set_cursor_pos(self, pos):
        self.cursor = pos

    def move_cursor_by_offset(self, offset):
        self.cursor += offset

    def peek_next_token(self):
        if self.cursor < len(self.tokens):
            token = self.tokens[self.cursor]
            return token
        return None

    def get_next_token(self):
        token = self.peek_next_token()
        if token is not None:
            self.cursor += 1
        return token


class Parser:
    def __init__(self, line, tokenizer):
        self.tokenizer = tokenizer
        self.line = line

    def expect(self, arg):
        token = self.tokenizer.peek_next_token()
        if token is not None and token[0] == arg:
            return self.tokenizer.get_next_token()
        return None

    def tokenize(self):
        return self.tokenizer.tokenize()

    def investigate(self, msg, pos0='', pos1=''):
        if pos0 == '':
            print(msg, self.line)
        elif pos1 == '':
            print(msg, "'"+pos0+"'", "from", self.line)
        else:
            print(msg, "'"+pos0+" "+pos1+"'", "from", self.line)

    def parse_line(self):
        return self.equation()

    @staticmethod
    def construct_line(root):
        pass

    def __create_term(self, child0, child1=None):
        if child1 is None:
            return AleaeMARLeaNode(NodeEnum.TERM, None, [child0])
        return AleaeMARLeaNode(NodeEnum.TERM, None, [child0, child1])

    def equation(self):
        pass

    def field(self, sub_root):
        pass


class AleaeTokenizer(Tokenizer):
    def __init__(self, line):
        super().__init__(line)

    def tokenize(self):
        num_field_sep = 0
        for token in self.equ:
            if re.fullmatch(r'\d+', token.strip()) is not None and num_field_sep < 2:
                self.tokens.append((NodeEnum.COEFF, token.strip()))
            elif re.fullmatch(r'\d+', token.strip()) is not None:
                self.tokens.append((NodeEnum.RATE, token.strip()))
            elif (re.fullmatch(rf'{MARLEA_ARROW}', token.strip()) is not None
                  or re.fullmatch(rf'{MARLEA_NULL}', token.strip()) is not None):
                self.investigate("Invalid use of MARLEA symbols:", token.strip())
                return False
            elif re.fullmatch(rf'{ALEAE_FIELD_SEPARATOR}', token.strip()) is not None:
                self.tokens.append((NodeEnum.FIELD_SEP, token.strip()))
                num_field_sep += 1
            elif re.fullmatch(r'[^+: ]+', token.strip()) is not None:
                self.tokens.append((NodeEnum.CHEM, token.strip()))
            elif re.fullmatch(rf'\d+{ALEAE_FIELD_SEPARATOR}', token.strip()) is not None:
                self.tokens.append((NodeEnum.COEFF, token.strip().strip(ALEAE_FIELD_SEPARATOR)))
                self.tokens.append((NodeEnum.FIELD_SEP, token.strip(r'\d+')))
                num_field_sep += 1
            elif re.fullmatch(rf'{ALEAE_FIELD_SEPARATOR}[^+: ]+', token.strip()) is not None:
                self.tokens.append((NodeEnum.FIELD_SEP, token.strip(r'[^+ ]+')))
                self.tokens.append((NodeEnum.CHEM, token.strip().strip(ALEAE_FIELD_SEPARATOR)))
                num_field_sep += 1
            elif re.fullmatch(rf'\d+{ALEAE_FIELD_SEPARATOR}[^+: ]+', token.strip()) is not None:
                self.tokens.append((NodeEnum.COEFF, re.sub(rf'(\d+){ALEAE_FIELD_SEPARATOR}([^+: ]+)', r'\1', token.strip())))
                self.tokens.append((NodeEnum.FIELD_SEP, re.sub(rf'\d+{ALEAE_FIELD_SEPARATOR}[^+: ]+', ALEAE_FIELD_SEPARATOR, token.strip())))
                self.tokens.append((NodeEnum.CHEM, re.sub(rf'(\d+){ALEAE_FIELD_SEPARATOR}[^+: ]+)', r'\2', token.strip())))
                num_field_sep += 1
            else:
                self.investigate("Unrecognized symbol:", "'"+token.strip()+"'")
                return False
        return True


class AleaeParser(Parser):
    def __init__(self, line, all_chems):
        super().__init__(line, AleaeTokenizer(line))
        self.all_chems = all_chems

    def parse_line(self):
        return self.equation()

    @staticmethod
    def construct_line(root):
        new_equ = ''
        for child in root.children:
            if child.type == NodeEnum.RATE:
                new_equ += child.value
            elif child.type == NodeEnum.FIELD:
                temp = child.children
                while temp is not None:
                    new_equ += temp.value[0][1] + " " + temp.value[1][1] + " "
                    temp = temp.children
                new_equ += ": "

        return new_equ

    @staticmethod
    def convert_tree_to_marlea(old_root, waste='', aether=[]):
        new_root = AleaeMARLeaNode(NodeEnum.EQUATION, None, [])

        for i in range(ReactionParts.NUM_FIELDS.value - 1):
            field = old_root.children[i]
            new_root.children.append(AleaeMARLeaNode(NodeEnum.FIELD, None, None))
            new_root.children[i].children = AleaeMARLeaNode(NodeEnum.TERM, None, None)
            temp_term = field.children
            new_node = new_root.children[i].children
            while temp_term is not None:
                if temp_term.value[0][1] in set(aether) and i == 0 or temp_term.value[0][1] == waste:
                    new_root.children[i].children = AleaeMARLeaNode(NodeEnum.MARLEA_NULL, MARLEA_NULL, None)
                elif temp_term.value[0][1] not in set(aether):
                    if temp_term.value[1][1] == '1': new_node.value = None, temp_term.value[0]
                    else: new_node.value = temp_term.value[1], temp_term.value[0]

                    if temp_term.children is not None:
                        new_node.children = AleaeMARLeaNode(NodeEnum.TERM, None, None)
                        new_node = new_node.children
                temp_term = temp_term.children
        return new_root


    def equation(self):
        root = AleaeMARLeaNode(NodeEnum.EQUATION, self.line, [])
        sep_pos = []

        while self.tokenizer.peek_next_token() is not None:
            token = self.expect(NodeEnum.FIELD_SEP)
            if token is not None:
                sep_pos.append(self.tokenizer.get_cursor_pos() - 1)
            else:
                self.tokenizer.move_cursor_by_offset(1)

        if len(sep_pos) != 2:
            self.investigate("Invalid use of field separators:", self.tokenizer.tokens[sep_pos[len(sep_pos)-1]][1])
            return None

        if len(self.tokenizer.tokens) < sep_pos[1] + 2:
            self.investigate("Empty rate field")
            return None
        elif self.tokenizer.get_cursor_pos() > sep_pos[1] + 2 or not self.tokenizer.tokens[sep_pos[1]+1][1].isnumeric():
            self.investigate("Invalid rate field:", self.tokenizer.tokens[sep_pos[1]+1][1])
            return None

        root.children.append(AleaeMARLeaNode(NodeEnum.FIELD, None, None))
        root.children.append(AleaeMARLeaNode(NodeEnum.FIELD, None, None))
        root.children.append(AleaeMARLeaNode(NodeEnum.RATE, self.tokenizer.tokens[sep_pos[1]+1][1], None))
        self.tokenizer.set_cursor_pos(0)

        if not self.field(root.children[0]): return None
        self.tokenizer.set_cursor_pos(sep_pos[0] + 1)
        if not self.field(root.children[1]): return None

        return root


    def field(self, sub_root):
        first_term = AleaeMARLeaNode(NodeEnum.TERM, None, None)

        cur_term = first_term
        token0, token1 = self.expect(NodeEnum.CHEM), self.expect(NodeEnum.COEFF)
        while token0 is not None and token1 is not None:
            if token0[1] not in self.all_chems:
                self.investigate("Chem missing in .in file:", self.tokenizer.check_token_at_cursor(-2)[1])
                return False

            cur_term.value = token0, token1
            token0, token1 = self.expect(NodeEnum.CHEM), self.expect(NodeEnum.COEFF)
            if token0 is not None and token1 is not None:
                cur_term.children = AleaeMARLeaNode(NodeEnum.TERM, None, None)
                cur_term = cur_term.children

        test_token = self.tokenizer.peek_next_token()
        if test_token is None or test_token[0] != NodeEnum.FIELD_SEP:
            self.investigate("Invalid term:", self.tokenizer.check_token_at_cursor(-1)[1],
                             self.tokenizer.check_token_at_cursor(0)[1])
            return False

        sub_root.children = first_term
        return True



class MARleaTokenizer(Tokenizer):
    def __init__(self, line):
        super().__init__(line)

    def tokenize(self):
        num_marlea_nulls = 0

        for i, token in enumerate(self.equ):
            if re.fullmatch(f'{MARLEA_ARROW}', token.strip()) is not None:
                self.tokens.append((NodeEnum.MARLEA_ARROW, token.strip()))
            elif re.fullmatch(f'{MARLEA_NULL}', token.strip()) is not None:
                self.tokens.append((NodeEnum.MARLEA_NULL, token.strip()))
                num_marlea_nulls += 1
            elif re.fullmatch(f'[{MARLEA_TERM_SEPARATOR}]', token.strip()) is not None:
                self.tokens.append((NodeEnum.TERM_SEP, token.strip()))
            elif re.fullmatch(r'\d+', token.strip()) is not None:
                self.tokens.append((NodeEnum.COEFF, token.strip()))
            elif re.fullmatch(r'[^+: ]+', token.strip()) is not None:
                self.tokens.append((NodeEnum.CHEM, token.strip()))
            else:
                self.investigate("Unrecognized symbol:", "'"+token.strip()+"'")
                return False
        return True


class MARleaParser(Parser):
    def __init__(self, line):
        super().__init__(line, MARleaTokenizer(line))
        self.found_chems = set()

    def parse_line(self):
        return self.equation()

    @staticmethod
    def construct_line(root):
        new_equ = ''

        for i, field in enumerate(root.children):
            temp = field.children
            while temp is not None:
                if temp.type == NodeEnum.MARLEA_NULL:
                    new_equ += temp.value
                elif temp.value[0] is not None:
                    new_equ += temp.value[0][1] + " " + temp.value[1][1]
                else:
                    new_equ += temp.value[1][1]

                temp = temp.children
                if temp is not None: new_equ += " + "

            if i < 1: new_equ += " => "

        return new_equ

    @staticmethod
    def convert_tree_to_aleae(old_root, rate, waste='', aether=[]):
        new_root = AleaeMARLeaNode(NodeEnum.EQUATION, None, [])

        aether_found = False
        for i in range(ReactionParts.NUM_FIELDS.value - 1):
            field = old_root.children[i]
            new_root.children.append(AleaeMARLeaNode(NodeEnum.FIELD, None, None))
            new_root.children[i].children = AleaeMARLeaNode(NodeEnum.TERM, None, None)
            temp_term = field.children
            new_node = new_root.children[i].children
            while temp_term is not None:
                if temp_term.type == NodeEnum.MARLEA_NULL:
                    if i == ReactionParts.REACTANTS.value and len(aether) > 0:
                        new_node.value = (NodeEnum.CHEM, aether[0]), (NodeEnum.COEFF, '1')
                        aether_found = True
                    elif i == ReactionParts.PRODUCTS.value and waste != '':
                        new_node.value = (NodeEnum.CHEM, waste), (NodeEnum.COEFF, '1')
                else:
                    if aether_found:
                        new_node.value = (NodeEnum.CHEM, aether[0]), (NodeEnum.COEFF, '1')
                        aether_found = False
                        new_node.children = AleaeMARLeaNode(NodeEnum.TERM, None, None)
                        new_node = new_node.children

                    if temp_term.value[0] is None:
                        new_node.value = temp_term.value[1], (NodeEnum.COEFF, "1")
                    else:
                        new_node.value = temp_term.value[1], temp_term.value[0]

                if temp_term.children is not None:
                    new_node.children = AleaeMARLeaNode(NodeEnum.TERM, None, None)
                    new_node = new_node.children
                temp_term = temp_term.children

        new_root.children.append(AleaeMARLeaNode(NodeEnum.RATE, rate, None))
        return new_root


    def equation(self):
        root = AleaeMARLeaNode(NodeEnum.EQUATION, self.line, [])
        sep_pos = 0
        num_marlea_arrows = 0

        while self.tokenizer.peek_next_token() is not None:
            token = self.expect(NodeEnum.MARLEA_ARROW)
            if token is not None:
                sep_pos = self.tokenizer.get_cursor_pos() - 1
                num_marlea_arrows += 1
            else:
                self.tokenizer.move_cursor_by_offset(1)

        if num_marlea_arrows != 1:
            self.investigate("Invalid or missing use of MARlea arrow:", self.tokenizer.tokens[sep_pos][1])
            return None

        root.children.append(AleaeMARLeaNode(NodeEnum.FIELD, None, None))
        root.children.append(AleaeMARLeaNode(NodeEnum.FIELD, None, None))
        self.tokenizer.set_cursor_pos(0)

        if not self.field(root.children[0]): return None
        self.tokenizer.set_cursor_pos(sep_pos + 1)
        if not self.field(root.children[1]): return None

        return root


    def field(self, sub_root):
        token = self.tokenizer.peek_next_token()
        if token is None or token[0] == NodeEnum.MARLEA_ARROW:
            self.investigate("Empty field")
            return False

        null_token = self.expect(NodeEnum.MARLEA_NULL)
        if null_token is not None:
            sub_root.children = AleaeMARLeaNode(NodeEnum.MARLEA_NULL, MARLEA_NULL, None)

            token0, token1 = self.expect(NodeEnum.MARLEA_ARROW), self.expect(NodeEnum.MARLEA_NULL)
            if token0 is None and self.tokenizer.get_cursor_pos() < len(self.tokenizer.tokens) or token1 is not None:
                self.investigate("Invalid use of MARlea NULL:", self.tokenizer.check_token_at_cursor(-1)[1])
                return False
            else: return True

        test_token = self.expect(NodeEnum.TERM_SEP)
        if test_token is not None:
            self.investigate("Invalid use of term seperator:", self.tokenizer.check_token_at_cursor(-1)[1])
            return False

        first_term = AleaeMARLeaNode(NodeEnum.TERM, None, None)

        cur_term = first_term
        token0 = self.expect(NodeEnum.CHEM)
        token1, token2 = None, None
        if token0 is None:
            token1, token2 = self.expect(NodeEnum.COEFF), self.expect(NodeEnum.CHEM)
        token_aux = self.expect(NodeEnum.TERM_SEP)

        while token0 is not None or token1 is not None or token2 is not None:
            if token0 is not None:
                cur_term.value = None, token0
                self.found_chems.add(token0[1])
            elif token1 is not None and token2 is not None:
                if token1[1] == "1":
                    self.investigate("Invalid term:", self.tokenizer.check_token_at_cursor(-3)[1],
                                     self.tokenizer.check_token_at_cursor(-2)[1])
                    return False
                else:
                    cur_term.value = token1, token2
                self.found_chems.add(token2[1])
            elif token1 is None or token2 is None:
                self.investigate("Invalid term:", self.tokenizer.check_token_at_cursor(-2)[1],
                                 self.tokenizer.check_token_at_cursor(-1)[1])
                return False

            test_token = self.tokenizer.peek_next_token()
            if test_token is not None and test_token[0] == NodeEnum.MARLEA_NULL:
                self.investigate("Invalid use of MARlea NULL:", self.tokenizer.check_token_at_cursor(0)[1])
                return False

            if token_aux is not None:
                if test_token is None or test_token[0] == NodeEnum.TERM_SEP:
                    self.investigate("Invalid use of term separator:", self.tokenizer.check_token_at_cursor(-1)[1])
                    return False
                elif test_token is not None:
                    cur_term.children = AleaeMARLeaNode(NodeEnum.TERM, None, None)
                    cur_term = cur_term.children
            else:
                if (test_token is not None and test_token[0] != NodeEnum.MARLEA_ARROW
                        and self.tokenizer.get_cursor_pos() < len(self.tokenizer.tokens)):
                    self.investigate("Invalid term:", self.tokenizer.check_token_at_cursor(-1)[1],
                                     self.tokenizer.check_token_at_cursor(0)[1])
                    return False

            token0 = self.expect(NodeEnum.CHEM)
            token1, token2 = None, None
            if token0 is None:
                token1, token2 = self.expect(NodeEnum.COEFF), self.expect(NodeEnum.CHEM)
            token_aux = self.expect(NodeEnum.TERM_SEP)

        sub_root.children = first_term
        return True


def check_aleae_in_line(in_line):
    """
    Checks whether a line is a valid initialization statement within an Aleae .in file
    :param in_line: a list containing the elements of an Aleae initialization statement
    :return: True if line is valid or False if it detects an error
    """
    threshold_sym = {"LE", "LT", "GE", "GT", "N"}
    if len(in_line) >= 4:
        print(".in line not three or four elements: ", in_line)
        return False
    elif in_line[0].strip().isnumeric():
        print("Chem can't be a number: ", in_line)
        return False
    elif not in_line[1].strip().isnumeric():
        print("Amount must be an integer:", in_line)
        return False
    elif in_line[2].strip() not in threshold_sym:
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
        if check_aleae_in_line(temp_row):
            input_file_reader_to_converter_auxilliary_queue.put(temp_row[0])

            if temp_row[1] != "0" and temp_row[0] not in set(aether):
                input_file_reader_to_output_writer_queue.put(temp_row[:2])
            temp = f_init.readline()
        else:
            print("Conversion has been halted. Any output MARlea file is considered unsuitable to run.")
            input_file_reader_to_converter_auxilliary_queue.put(END_PROCEDURE)
            input_file_reader_to_output_writer_queue.put(END_PROCEDURE)

    f_init.close()

    input_file_reader_to_output_writer_queue.put([])
    input_file_reader_to_converter_auxilliary_queue.put(END_PROCEDURE)
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

    all_chems = set()
    temp = input_file_reader_to_converter_auxilliary_queue.get()
    while temp != END_PROCEDURE:                                            # Get all chems to feed to the parser
        all_chems.add(temp)
        temp = input_file_reader_to_converter_auxilliary_queue.get()

    temp = input_file_reader_to_converter_queue.get()
    while temp != END_PROCEDURE:
        a_parser = AleaeParser(temp, all_chems)
        if not a_parser.tokenize():                                         # Tokenize the reaction
            print("Conversion has been halted. Any output MARlea file is considered unsuitable to run.")
            break

        aleae_tree = a_parser.parse_line()                                  # Parse reaction
        print("Conversion has been halted. Any output MARlea file is considered unsuitable to run.")
        if aleae_tree is None:
            break

        marlea_tree = AleaeParser.convert_tree_to_marlea(aleae_tree, waste, aether)     # Convert reaction
        print("Conversion has been halted. Any output MARlea file is considered unsuitable to run.")
        if marlea_tree is None:
            break

        temp_list = temp.strip().split(ALEAE_FIELD_SEPARATOR)
        converted_reaction = MARleaParser.construct_line(marlea_tree)
        converter_to_output_file_writer_queue_0.put([converted_reaction," "+temp_list[2].strip()])

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
        writer.writerow(temp)                                               # Write processed line from converter
        temp = converter_to_output_file_writer_queue_0.get()

    f_MARlea_output.close()


def read_marlea_file(MARlea_input_filename):
    """
    Read each row from a MARlea input file, pre-process said row, and send it to either a converter or writer.
    :param MARlea_input_filename: name of MARlea file as input
    """
    f_MARlea_input = open_file_read(MARlea_input_filename)
    if f_MARlea_input is None:
        input_file_reader_to_converter_queue.put(END_PROCEDURE)
        input_file_reader_to_output_writer_queue.put(END_PROCEDURE)
        return
    reader = csv.reader(f_MARlea_input, "excel")

    for row in reader:
        if len(row) > 0 and "//" not in row[1] and "//" not in row[0]:       # Filter out row without initialized chemicals or reactions
            if MARLEA_ARROW in row[0]:
                input_file_reader_to_converter_queue.put(row)                # Send any reactions to the converter
            elif row[1] != "" and row[0] != "":
                if check_marlea_init(row):
                    input_file_reader_to_output_writer_queue.put(row[0].strip() + " " + row[1].strip() + ' N\n')
                    input_file_reader_to_converter_auxilliary_queue.put(row)
                else:
                    print("Conversion has been halted. Any output Aleae file is considered unsuitable to run.")
                    break

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
        m_parser = MARleaParser(temp[0])                                                # Tokenize the reaction
        if not m_parser.tokenize():
            print("Conversion has been halted. Any output Aleae file is considered unsuitable to run.")
            break

        marlea_tree = m_parser.parse_line()                                             # Parse reaction
        if marlea_tree is None:
            print("Conversion has been halted. Any output Aleae file is considered unsuitable to run.")
            break

        aleae_tree = MARleaParser.convert_tree_to_aleae(marlea_tree, temp[1], waste, aether)        # Convert reaction
        if aleae_tree is None:
            print("Conversion has been halted. Any output Aleae file is considered unsuitable to run.")
            break

        converted_reaction = AleaeParser.construct_line(aleae_tree)

        for chem in m_parser.found_chems:
            if chem not in set(found_chems.keys()):
                if len(aether) > 0 and chem == aether[0]:                        # Add discovered chemical to found_chems
                    found_chems[chem] = '1'
                else:
                    found_chems[chem] = '0'
                converter_to_output_file_writer_queue_0.put(chem + " " + found_chems[chem] + ' N\n')
        converter_to_output_file_writer_queue_1.put(converted_reaction+"\n")

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

    input_files = []
    pipeline_enabled = False
    output_files = []

    if sys.version_info.major < 3 and sys.version_info.minor < 8:
        print("Version of Python must be 3.8 or higher")
        exit(0)

    # All the commands and their associated flags
    main_parser = argparse.ArgumentParser(prog="converter.py", add_help=True)
    subparsers = main_parser.add_subparsers(dest="command", required=True)

    a_to_m_parser = subparsers.add_parser("a-to-m", usage="Convert Aleae files into MARlea files", help="Convert Aleae files to an MARlea equivalent")
    a_to_m_parser.add_argument("-i", "--input", action='store', nargs=2, required=True, help="Paths to the .in and .r Aleae files")
    a_to_m_parser.add_argument("-p", "--pipeline_enable", action='store_true', help="Enable pipelined Execution of file conversion")
    a_to_m_parser.add_argument("-o", "--output", action='store', required=True, help="Path to new or preexisting MARlea file")
    a_to_m_parser.add_argument("--waste", action='store', required=False, help="A chemical that is the waste products of reactions")
    a_to_m_parser.add_argument("--aether", action='store', nargs='*', help="A list of chemicals that enable continous production of other chemicals")

    m_to_a_parser = subparsers.add_parser("m-to-a", usage="Convert MARlea files into Aleae files", help="Convert MARlea file to Aleae equivalents")
    m_to_a_parser.add_argument("-i", "--input", action='store', required=True, help="Paths to .csv MARlea file")
    m_to_a_parser.add_argument("-p", "--pipeline_enable", action='store_true', help="Enable pipelined Execution of file conversion")
    m_to_a_parser.add_argument("-o", "--output", action='store', nargs=2, required=True, help="Paths to new or preexisting .in and .r Aleae files")
    m_to_a_parser.add_argument("--waste", action='store', required=False, help="A chemical that is the waste products of reactions")
    m_to_a_parser.add_argument("--aether", action='store', nargs='*', help="A list of chemicals that enable continous production of other chemicals")

    gui_parser = subparsers.add_parser("gui", usage="summons the gui", help="Summon the program's graphical user interface")
    gui_parser.add_argument("-v", "--verbose", action='store_true', help="This argument has no function at the moment")

    parsed_args = main_parser.parse_args(sys.argv[1:])  # Extract some of the arguments from the command-line input
    input_mode = parsed_args.command

    if input_mode != "gui":
        if parsed_args.waste is not None:
            waste_local = parsed_args.waste

        if parsed_args.aether is not None:
            aether_local = parsed_args.aether
            for elem in aether_local:
                if elem == waste_local:
                    print("Error: Aether chemical", elem, "is the same as", waste_local)
                    exit(0)

        input_files = parsed_args.input                             # Extract the rest of the command-line input
        output_files = parsed_args.output
        pipeline_enabled = parsed_args.pipeline_enable

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

        start_m_to_a_conversion(aleae_in_filename, aleae_r_filename, marlea_filename, waste_local, aether_local,
                         pipeline_enabled)
    elif input_mode == "gui":
        gui_root.mainloop()
        exit(0)
    else:
        print("Error: Invalid command.")
        exit(-1)


scan_args()
