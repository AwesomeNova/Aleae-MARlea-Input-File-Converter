"""
Name: AwesomeNova
Updated at: 10/6/2024

Script for converting Aleae files into MARlea ones and vice versa via sequential or pipelined execution. Please read the
README to learn how to use it. The script does not check for whether an input file given to it is valid, specified by the
documentation of Aleae and MARlea, but any converted file will be valid if a given input file or set of files is valid.

There are no known bugs found in the code at the moment. However, if you encountered a bug or issue while using this script,
please send an issue on the GitHub repo or push a fix of the code on a separate branch and make a pull request.
"""

import os.path
import sys
import csv
from enum import Enum
from enum import IntEnum
from queue import Queue
from threading import Thread

ALEAE_FIELD_SEPARATOR = ':'
MARLEA_TERM_SEPARATOR = '+'
MARLEA_ARROW = "=>"
MARLEA_NULL = 'NULL'

input_file_reader_to_converter_queue = Queue()                  # Setup queues for inter-thread communication
input_file_reader_to_output_writer_queue = Queue()
input_file_reader_to_converter_auxilliary_queue = Queue()
converter_to_output_file_writer_queue_0 = Queue()
converter_to_output_file_writer_queue_1 = Queue()
END_PROCEDURE = "fin"

class ArgPosition(IntEnum):
    MODE = 1
    MARLEA_INPUT_FILE = 2
    IN_INPUT_FILE = 2
    R_INPUT_FILE = 3
    OUTPUT_FLAG_A = 4
    OUTPUT_FLAG_M = 3
    IN_OUTPUT_FILE = 4
    R_OUTPUT_FILE = 5
    MARLEA_OUTPUT_FILE = 5
    WASTE_AETHER = 6
    AETHER_EXCLUSIVE = 7
    MAX_COMMAND_LINE_LEN = 8
    MIN_COMMAND_LINE_LEN = 6


class ReactionParts(IntEnum):
    REACTANTS = 0
    PRODUCTS = 1
    REACTION_RATE = 2
    NUM_FIELDS = 3


class Flags(Enum):
    A_TO_M = "--a_to_m"
    M_TO_A = "--m_to_a"
    SEQUENTIAL_OUTPUT = "--sequential_output"
    PIPELINE_OUTPUT = "--pipeline_output"


def process_flag(flag):
    """ The function parses a flag given as input and return an enum representation of the input flag if successful or
    the return value of alt_flag() if a ValueError exception was thrown"""

    try:
        return Flags(flag)
    except ValueError:
        return alt_flag(flag)


def alt_flag(flag):
    """The function parses a flag that has thrown a ValueError exception in process_flag(). It return the enum if the
    flag is matched successfully and None otherwise."""
    match flag:
        case "-a":
            return Flags("--a_to_m")
        case "-m":
            return Flags("--m_to_a")
        case "-s":
            return Flags("--sequential_output")
        case "-p":
            return Flags("--pipeline_output")
        case _:
            return None


def is_valid_flag(flag):
    """The function checks if a flag is valid."""
    match flag:
        case "--a_to_m" | "--m_to_a" | "--output":
            return True
        case "-a" | "-m" | "-s" | "-p":
            return True
        case _:
            return False

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
            print("Input file " + filename + " has invalid file type")
    else:
        try:
            return open(filename, "x", newline='')
        except OSError:
            print("Input file " + filename + " has invalid file type")
    return None


def remove_empty_str_elems(lst):
    return [i for i in lst if i != ""]


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
                    if temp_term[0] == aether[0]:                                       # Add discovered chemical to found_chems
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


def scan_args():
    """
    The function interprets the command-line input and parses it for any information needed to start converting input
    files. All error correction is handled in this function.
    """
    aether_local = []
    waste_local = ""

    if sys.version_info.major < 3 and sys.version_info.minor < 10:
        print("Version of Python must be 3.10 or higher")
        return
    if len(sys.argv) < ArgPosition.MIN_COMMAND_LINE_LEN.value:
        print("Error: No or too few arguments provided")
        exit(-1)

    input_mode = process_flag(sys.argv[ArgPosition.MODE.value])
    if input_mode is None:
        print("Error: Arguments provided are invalid")
        exit(-1)
    elif len(sys.argv) > ArgPosition.MAX_COMMAND_LINE_LEN.value:
        print("Error: Too many arguments provided")
        exit(-1)

    if len(sys.argv) >= 7:
        if "waste=" in sys.argv[ArgPosition.WASTE_AETHER.value]:
            waste_local = sys.argv[ArgPosition.WASTE_AETHER.value].strip("waste=")
        elif "aether=[" in sys.argv[ArgPosition.WASTE_AETHER.value]:
            aether_local = sys.argv[ArgPosition.WASTE_AETHER.value].strip("aether[=").strip(']').split(',')
        elif "aether=" in sys.argv[ArgPosition.WASTE_AETHER.value]:
            test = sys.argv[ArgPosition.WASTE_AETHER.value].strip("aether=").split(',')
            aether_local = sys.argv[ArgPosition.WASTE_AETHER.value].strip("aether=").split(',')
        else:
            print("Error: invalid name for aether and/or waste")
            exit(-1)
    if len(sys.argv) >= 8:
        if "aether=[" in sys.argv[ArgPosition.AETHER_EXCLUSIVE.value]:
            aether_local = sys.argv[ArgPosition.AETHER_EXCLUSIVE.value].strip("aether[=").strip(']').split(',')
        elif "aether=" in sys.argv[ArgPosition.AETHER_EXCLUSIVE.value]:
            aether_local = sys.argv[ArgPosition.AETHER_EXCLUSIVE.value].strip("aether=").split(',')
        else:
            print("Error: invalid name for aether")
            exit(-1)

    if input_mode == Flags.A_TO_M:
        if not is_valid_flag(sys.argv[ArgPosition.OUTPUT_FLAG_A.value]):
            print("Error: Invalid output flag")
            print(sys.argv[ArgPosition.OUTPUT_FLAG_A.value])
            exit(-1)

        if ".in" not in sys.argv[ArgPosition.IN_INPUT_FILE.value] or ".r" not in sys.argv[ArgPosition.R_INPUT_FILE.value]:
            print("Error: Invalid input file type")
            exit(-1)
        if ".csv" not in sys.argv[ArgPosition.MARLEA_OUTPUT_FILE.value]:
            print("Error: Invalid output file type")
            exit(-1)

        output_mode = process_flag(sys.argv[ArgPosition.OUTPUT_FLAG_A.value])

        aleae_in_filename = sys.argv[ArgPosition.IN_INPUT_FILE.value]
        aleae_r_filename = sys.argv[ArgPosition.R_INPUT_FILE.value]
        marlea_filename = sys.argv[ArgPosition.MARLEA_OUTPUT_FILE.value]
        if output_mode == Flags.PIPELINE_OUTPUT:
            reader_in_thread = Thread(None, read_aleae_in_file, None, [aleae_in_filename, aether_local, ])
            reader_r_thread = Thread(None, read_aleae_r_file, None, [aleae_r_filename, ])
            converter_thread = Thread(None, aleae_to_marlea_converter, None, [waste_local, aether_local, ])
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
            read_aleae_in_file(aleae_in_filename, aether_local)
            read_aleae_r_file(aleae_r_filename)
            aleae_to_marlea_converter(waste_local, aether_local)
            write_marlea_file(marlea_filename)
    elif input_mode == Flags.M_TO_A:
        if ".csv" not in sys.argv[ArgPosition.MARLEA_INPUT_FILE.value]:
            print("Error: Invalid input file type")
            exit(-1)
        if not is_valid_flag(sys.argv[ArgPosition.OUTPUT_FLAG_M.value]):
            print("Error: Invalid flag")
            exit(-1)
        if ".in" not in sys.argv[ArgPosition.IN_OUTPUT_FILE.value] or ".r" not in sys.argv[ArgPosition.R_OUTPUT_FILE.value]:
            print("Error: Invalid output file type")
            exit(-1)

        output_mode = process_flag(sys.argv[ArgPosition.OUTPUT_FLAG_M.value])

        marlea_filename = sys.argv[ArgPosition.MARLEA_INPUT_FILE.value]
        aleae_in_filename = sys.argv[ArgPosition.IN_OUTPUT_FILE.value]
        aleae_r_filename = sys.argv[ArgPosition.R_OUTPUT_FILE.value]

        if output_mode == Flags.PIPELINE_OUTPUT:
            reader_thread = Thread(None, read_marlea_file, None, [marlea_filename, ])
            converter_thread = Thread(None, marlea_to_aleae_converter, None, [waste_local, aether_local, ])
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
            marlea_to_aleae_converter(waste_local, aether_local)
            write_aleae_in_file(aleae_in_filename)
            write_aleae_r_file(aleae_r_filename)
    else:
        print("Error: Invalid flag" + sys.argv[ArgPosition.MODE.value])


scan_args()
