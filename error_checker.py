"""
Name: AwesomeNova
Updated at: 10/12/2024

Script for checking Aleae or MARlea files the functions contained in this file are also in converter.py. This file may
become deprecated or be moved to a separate repo.

This is the template for all command-line inputs to the script:
'python error_checker.py check <--input type flag> <input file(s)>'

There are no major bugs found in the code at the moment. However, if you encountered a bug or issue while using this script,
please send an issue on the GitHub repo or push a fix of the code on a separate branch and make a pull request.
"""

import argparse
import csv
import os
import sys

ALEAE_FIELD_SEPARATOR = ':'
MARLEA_TERM_SEPARATOR = '+'
MARLEA_ARROW = "=>"
MARLEA_NULL = 'NULL'


def open_file_read(filename):
    """The function attempts to open an input file for reading."""
    if os.path.isfile(filename):
        try:
            return open(filename, "r", newline='')
        except OSError:
            print("Input file " + filename + " has invalid file type")
    return None


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

main_parser = argparse.ArgumentParser(prog="error_checker.py", add_help=True)
subparsers = main_parser.add_subparsers(dest="command")

error_parser = subparsers.add_parser("check")
error_parser.add_argument("-a", "--aleae", action='store', nargs=2)
error_parser.add_argument("-m", "--marlea", action='store')

parsed_args = main_parser.parse_args(sys.argv[1:])

if parsed_args.aleae is not None:
    input_files = parsed_args.aleae
    check_aleae_files(input_files[0], input_files[1])
elif parsed_args.marlea is not None:
    input_files = parsed_args.marlea
    check_marlea_file(input_files)

