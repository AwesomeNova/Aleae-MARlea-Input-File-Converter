import argparse
import csv
import os
import sys

ALEAE_FIELD_SEPARATOR = ':'
MARLEA_TERM_SEPARATOR = '+'
MARLEA_ARROW = "=>"


def open_file_read(filename):
    """The function attempts to open an input file for reading."""
    if os.path.isfile(filename):
        try:
            return open(filename, "r", newline='')
        except OSError:
            print("Input file " + filename + " has invalid file type")
    return None


def check_aleae_in_line(temp_line):
    threshold_sym = {"LE", "LT", "GE", "GT", "N"}
    if len(temp_line) != 3:
        print(".in line not three elements: ", temp_line)
        return False
    elif temp_line[0].strip().isnumeric():
        print("Chem can't be a number: ", temp_line)
        return False
    elif not temp_line[1].strip().isnumeric():
        print("Amount must be an integer:", temp_line)
        return False
    elif temp_line[2] not in threshold_sym:
        print("Invalid threshold: ", temp_line)
        return False
    return True


def check_aleae_r_line(temp_line, chems):
    if len(temp_line) != 3:
        print("Need three fields: ", temp_line)
        return False
    if not temp_line[2].strip().isnumeric():
        print("Rate must be a number: ", temp_line[2].strip())
        return False

    for i in range(2):
        temp_field = temp_line[i].strip().split()
        if len(temp_field) % 2 == 1:
            print("Invalid reaction format: ", temp_line)
            return False
        for j in range(0, len(temp_field), 2):
            if temp_field[j].strip().isnumeric() or not temp_field[j + 1].strip().isnumeric():
                print("invalid term: " + temp_field[j] + " " + temp_field[j + 1])
                return False
            elif temp_field[j].strip() not in chems:
                print("chem in reaction is not initialized: ", temp_field[j])
                return False
    return True


def check_aleae_files(aleae_in_filename, aleae_r_filename):
    f_init = open_file_read(aleae_in_filename)
    if f_init is None:
        return

    temp = f_init.readline()
    chems = set()
    while temp != "":
        temp_line = temp.strip().split()
        if len(temp_line) < 1:
            temp = f_init.readline()
            continue
        if not check_aleae_in_line(temp_line):
            return

        chems.add(temp_line[0])
        temp = f_init.readline()
    f_init.close()

    f_react = open_file_read(aleae_r_filename)
    if f_react is None:
        return

    temp = f_react.readline()
    while temp != "":
        temp_line = temp.strip().split(":")
        if len(temp_line) < 1:
            continue
        if not check_aleae_r_line(temp_line, chems):
            return
        temp = f_react.readline()
    f_react.close()

    print("Success")


def check_marlea_line(row):
    temp_fields = row[0].strip().split(MARLEA_ARROW)
    print(temp_fields)
    for i in range(2):
        if len(temp_fields) > 2:
            print("Invalid reaction formant: " + temp_fields)
            return False

        temp_terms = temp_fields[i].strip().split(MARLEA_TERM_SEPARATOR)

        for term in temp_terms:
            print(term)
            t = term.strip().split()

            if len(t) == 1 and not t[0].isnumeric():
                continue
            elif len(t) == 2 and t[0].isnumeric() and not t[1].isnumeric():
                continue
            else:
                print("invalid term: " + t[0] + ' ' + t[1])
                return False
    return True


def check_marlea_file(MARlea_input_filename):
    f_MARlea_input = open_file_read(MARlea_input_filename)
    if f_MARlea_input is None:
        return

    reader = csv.reader(f_MARlea_input, "excel")
    counter= 0
    for row in reader:
        if len(row) < 1:
            continue
        elif row[1] == "" or row[0] == "":
            continue
        elif row[1].strip().isnumeric():
            if row[0].strip().isnumeric():
                print("Invalid row: ", row)
                return
            elif len(row[0].strip().split()) < 2:
                continue
        if "//" not in row[1] and "//" not in row[0] and MARLEA_ARROW in row[0]:
            if not check_marlea_line(row):
                return
    f_MARlea_input.close()
    print("success")

main_parser = argparse.ArgumentParser(prog="error_checker.py", add_help=True)
subparsers = main_parser.add_subparsers(dest="command")

error_parser = subparsers.add_parser("check")
error_parser.add_argument("-a", "--aleae", action='store', nargs=2)
error_parser.add_argument("-m", "--marlea", action='store')

parsed_args = main_parser.parse_args(sys.argv[1:])

aleae_files = parsed_args.aleae
marlea_file = parsed_args.marlea

if aleae_files is not None:
    print(aleae_files)
    check_aleae_files(aleae_files[0], aleae_files[1])
elif marlea_file is not None:
    print(marlea_file)
    check_marlea_file(marlea_file)
