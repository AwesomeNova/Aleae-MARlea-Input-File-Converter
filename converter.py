import os.path
import sys
import csv
from enum import Enum
from enum import IntEnum

MARLEA_ARROW = "=>"
MARLEA_NULL = 'NULL'


class ReactionParts(IntEnum):
    REACTANTS = 0
    PRODUCTS = 1
    REACTION_RATE = 2
    NUM_FIELDS = 3


class Flags(Enum):
    A_TO_M = "--a_to_m"
    M_TO_A = "--m_to_a"
    OUTPUT = "--output"


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
        case "-o":
            return Flags("--output")
        case _:
            return None


def is_valid_flag(flag):
    """The function checks if a flag is valid."""
    match flag:
        case "--a_to_m" | "--m_to_a" | "--output":
            return True
        case "-a" | "-m" | "-o":
            return True
        case _:
            return False


def open_aleae_file_read(filename):
    """The function attempts to open an Aleae input file for reading."""
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


def open_marlea_file_read(filename):
    """The function attempts to open an MARlea input file for reading."""
    if os.path.isfile(filename):
        try:
            return open(filename, 'r', newline='')
        except OSError:
            print("Input file " + filename + " has invalid file type")
    return None


def remove_empty_str_elems(lst):
    return [i for i in lst if i != ""]


def convert_aleae_to_marlea(aleae_in_filename, aleae_r_filename, MARlea_output_filename, waste, aether):
    """
    The function converts Aleae .in and .r files into one MARlea file.
    :param aleae_in_filename: name of Aleae .in file
    :param aleae_r_filename: name of Aleae .r file
    :param MARlea_output_filename: name of MARlea file
    :param waste: a specified chemical that will be converted to a NULL in the products
    :param aether: list of chemicals that will be converted to a NULL in the reactants
    """
    MARlea_output_lst = []

    f_init = open_aleae_file_read(aleae_in_filename)
    if f_init is None:
        return

    temp = f_init.readline()
    while temp != "":                                                           # Convert .in file to beginning of MARlea file
        temp_row = temp.split(" ")
        if temp_row[1] != "0" and temp_row[0] not in set(aether):
            MARlea_output_lst.append(temp_row[:2])
        temp = f_init.readline()
    f_init.close()
    MARlea_output_lst.append([])

    f_react = open_aleae_file_read(aleae_r_filename)
    if f_react is None:
        return
    temp = f_react.readline()

    while temp != "":
        converted_reaction = []
        temp_row = temp.split(":")                                              # Split reactants, products, and rates into elements of list called temp_row

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
                            converted_reaction_str += "+ "
                if i == ReactionParts.REACTANTS.value:
                    converted_reaction_str += "=> "

        MARlea_output_lst.append(converted_reaction)
        temp = f_react.readline()

    f_MARlea_output = open_file_write(MARlea_output_filename)
    if f_MARlea_output is None:
        return

    writer = csv.writer(f_MARlea_output, "excel")
    for elem in MARlea_output_lst:
        writer.writerow(elem)
    f_MARlea_output.close()


def convert_marlea_to_aleae(MARlea_input_filename, aleae_in_filename, aleae_r_filename, waste, aether):
    """
    The function converts a MARlea file into Aleae .in and .r files
    :param MARlea_input_filename: name of MARlea file as input
    :param aleae_in_filename: name of Aleae .in file as output
    :param aleae_r_filename: name of Aleae .r file as output
    :param waste: a specified chemical that will be converted to a NULL in the products
    :param aether: list of chemicals that will be converted to a NULL in the reactants
    """
    if ".csv" in MARlea_input_filename:
        f_MARlea_input = open_marlea_file_read(MARlea_input_filename)
        if f_MARlea_input is None:
            return
        reader = csv.reader(f_MARlea_input, "excel")
        MARlea_input_lst = []
        for row in reader:
            MARlea_input_lst.append(row)
    else:
        print(".csv" in MARlea_input_filename)
        print("Input file " + MARlea_input_filename + " has invalid file type")
        return

    chem_reactions_lst = []
    init_chems = dict()
    known_chems = []

    for i in range(len(MARlea_input_lst)):
        chem_reaction_str = ""

        if len(MARlea_input_lst[i]) > 0 and MARLEA_ARROW in MARlea_input_lst[i][0]:         # If line contains a reaction
            temp_rate = MARlea_input_lst[i][1].strip()
            temp_reaction_pieces = MARlea_input_lst[i][0].split(MARLEA_ARROW)               # Split reactions into reactants and products

            aether_loc_found = False
            for j in range(ReactionParts.NUM_FIELDS.value - 1):                             # MARlea only contains two relevant fields: reaction and rate
                temp_reaction_terms = temp_reaction_pieces[j].strip().split('+')            # Split reactants/products into terns
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

                    if temp_term[0] not in set(known_chems):                                # Add discovered chemical to known chems
                        known_chems.append(temp_term[0])
                        if temp_term[0] == aether[0]:
                            init_chems[temp_term[0]] = '1'
                        else:
                            init_chems[temp_term[0]] = '0'

                    chem_reaction_str += " "
                if j == ReactionParts.REACTANTS.value:
                    chem_reaction_str += ": "

            chem_reaction_str = chem_reaction_str.strip()
            chem_reactions_lst.append(chem_reaction_str + " : " + temp_rate)
        elif len(MARlea_input_lst[i]) > 0:                                          # If line contains initial state of chemicals
            temp_chem = MARlea_input_lst[i][0]
            if temp_chem not in set(known_chems) and temp_chem not in set(aether):
                known_chems.append(temp_chem)
                init_chems[MARlea_input_lst[i][0]] = MARlea_input_lst[i][1]

    f_aleae_output_in = open_file_write(aleae_in_filename)
    if f_aleae_output_in is None:
        return
    for elem in known_chems:
        f_aleae_output_in.write(elem.strip() + " " + init_chems[elem].strip() + ' N\n')
    f_aleae_output_in.close()

    f_aleae_output_r = open_file_write(aleae_r_filename)
    if f_aleae_output_r is None:
        return
    for elem in chem_reactions_lst:
        f_aleae_output_r.write(elem + "\n")
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
    if len(sys.argv) < 6:
        print("Error: No or too few arguments provided")
        exit(-1)

    mode = process_flag(sys.argv[1])
    if mode is None:
        print("Error: Arguments provided are invalid")
        exit(-1)
    elif len(sys.argv) > 8:
        print("Error: Too many arguments provided")
        exit(-1)

    if len(sys.argv) >= 7:
        if "waste=" in sys.argv[6]:
            waste_local = sys.argv[6].strip("waste=")
        elif "aether=[" in sys.argv[6]:
            aether_local = sys.argv[6].strip("aether[=").strip(']').split(',')
        elif "aether=" in sys.argv[6]:
            aether_local = sys.argv[6].strip("aether=").split(',')
        else:
            print("Error: invalid name for aether and/or waste")
            exit(-1)
    if len(sys.argv) >= 8:
        if "aether=[" in sys.argv[7]:
            aether_local = sys.argv[7].strip("aether[=").strip(']').split(',')
        elif "aether=" in sys.argv[7]:
            aether_local = sys.argv[7].strip("aether=").split(',')
        else:
            print("Error: invalid name for aether")
            exit(-1)

    if mode == Flags.A_TO_M:
        if not is_valid_flag(sys.argv[4]):
            print("Error: Invalid flag")
            print(sys.argv[4])
            exit(-1)

        if ".in" not in sys.argv[2] or ".r" not in sys.argv[3]:
            print("Error: Invalid input file type")
            exit(-1)
        if ".csv" not in sys.argv[5]:
            print("Error: Invalid output file type")
            exit(-1)

        aleae_in_filename = sys.argv[2]
        aleae_r_filename = sys.argv[3]
        marlea_filename = sys.argv[5]
        convert_aleae_to_marlea(aleae_in_filename, aleae_r_filename, marlea_filename, waste_local, aether_local)
    elif mode == Flags.M_TO_A:
        if ".csv" not in sys.argv[2]:
            print("Error: Invalid input file type")
            exit(-1)
        if not is_valid_flag(sys.argv[3]):
            print("Error: Invalid flag")
            exit(-1)
        if ".in" not in sys.argv[4] or ".r" not in sys.argv[5]:
            print("Error: Invalid output file type")
            exit(-1)

        marlea_filename = sys.argv[2]
        aleae_in_filename = sys.argv[4]
        aleae_r_filename = sys.argv[5]
        convert_marlea_to_aleae(marlea_filename, aleae_in_filename, aleae_r_filename, waste_local, aether_local)
    else:
        print("Error: Invalid flag" + sys.argv[1])


scan_args()
