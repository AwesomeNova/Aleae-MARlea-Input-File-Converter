import os.path
import sys
import csv
from enum import Enum

print(sys.argv[1:])


class Flags(Enum):
    A_TO_M = "--a_to_m"
    M_TO_A = "--m_to_a"
    OUTPUT = "--output"


def process_flag(flag):
    try:
        return Flags(flag)
    except ValueError:
        return alt_flag(flag)


def alt_flag(flag):
    match flag:
        case "-a":
            return Flags("--a_to_m")
        case "-m":
            return Flags("--m_to_a")
        case "-o":
            return Flags("--output")
        case _:
            return False


def is_valid_flag(flag):
    match flag:
        case "--a_to_m" | "--m_to_a" | "--output":
            return True
        case "-a" | "-m" | "-o":
            return True
        case _:
            return False


def open_aleae_file(str_file):
    try:
        return open(str_file, "r", newline='')
    except OSError:
        print("Input file " + str_file + " has invalid file type")
        return None


def open_aleae_file_write(str_file):
    if os.path.isfile(str_file):
        try:
            return open(str_file, "w", newline='')
        except OSError:
            print("Input file " + str_file + " has invalid file type")
            return None
    else:
        try:
            return open(str_file, "x", newline='')
        except OSError:
            print("Input file " + str_file + " has invalid file type")
            return None


def open_marlea_file(str_file, mode):
    try:
        return open(str_file, mode, newline='')
    except OSError:
        print("Input file " + str_file + " has invalid file type")
        return None


def remove_empty_str_elems(lst):
    return [i for i in lst if i != ""]


def write_to_marcea_out(aleae_in_str, aleae_r_str, MARlea_output_str, waste, aether):
    MARlea_output_lst = []

    f_init = open_aleae_file(aleae_in_str)
    if f_init is None:
        return
    temp = f_init.readline()
    while temp != "":
        temp_row = temp.split(" ")
        if temp_row[1] != "0" and temp_row[0] not in set(aether):
            MARlea_output_lst.append(temp_row[:2])
        temp = f_init.readline()
    f_init.close()
    MARlea_output_lst.append([])

    f_react = open_aleae_file(aleae_r_str)
    if f_react is None:
        return
    temp = f_react.readline()

    while temp != "":
        temp_out = []
        temp_row = temp.split(":")

        temp_out_str = ""
        for m in range(3):
            temp_row_piece = remove_empty_str_elems(temp_row[m].split(" "))
            if len(temp_row_piece) > 1:
                for i in range(0, len(temp_row_piece), 2):
                    (temp_row_piece[i], temp_row_piece[i + 1]) = (temp_row_piece[i + 1], temp_row_piece[i])
            if m == 2:
                temp_rate = temp_row_piece[0].strip()
                temp_out.append(temp_out_str.strip())
                temp_out.append(" " + temp_rate)
            else:
                k = 0
                while k < len(temp_row_piece):
                    if (m == 0 and temp_row_piece[k] in set(aether)) or (m == 1 and temp_row_piece[k] == waste):
                        temp_row_piece[k] = "NULL"
                        temp_out_str += temp_row_piece[k] + " "
                    elif not temp_row_piece[k] in set(aether):
                        if temp_row_piece[k] != "1":
                            temp_out_str += temp_row_piece[k] + " "
                        if temp_row_piece[k] == waste:
                            temp_row_piece[k] = "NULL"
                            temp_out_str += temp_row_piece[k] + " "
                        if not temp_row_piece[k].isnumeric() and k < len(temp_row_piece) - 1:
                            temp_out_str += "+ "
                    k += 1
                if m == 0:
                    temp_out_str += "=> "

        MARlea_output_lst.append(temp_out)
        temp = f_react.readline()

    if MARlea_output_str != "":
        if os.path.isfile(MARlea_output_str):
            f_MARlea_output = open_marlea_file(MARlea_output_str, "w")
        else:
            f_MARlea_output = open_marlea_file(MARlea_output_str, "x")

        if f_MARlea_output is None:
            return
    else:
        print("File path not provided for MARlea output file\n")
        return
    writer = csv.writer(f_MARlea_output, "excel")
    for elem in MARlea_output_lst:
        writer.writerow(elem)
    f_MARlea_output.close()


def write_to_aleae_out(MARlea_input_str, aleae_in_str, aleae_r_str, waste, aether):
    if ".csv" in MARlea_input_str:
        f_MARlea_input = open_marlea_file(MARlea_input_str, "r")
        if f_MARlea_input is None:
            return
        reader = csv.reader(f_MARlea_input, "excel")
        MARlea_input_lst = []
        for row in reader:
            MARlea_input_lst.append(row)
    else:
        print(".csv" in MARlea_input_str)
        print("Input file " + MARlea_input_str + " has invalid file type")
        return

    temp_out_row = []
    temp_chems = dict()
    known_chems = []

    for i in range(len(MARlea_input_lst)):
        temp_out_str = ""

        if len(MARlea_input_lst[i]) > 0 and "=>" in MARlea_input_lst[i][0]:
            temp_rate = MARlea_input_lst[i][1].strip()
            temp_reaction = MARlea_input_lst[i][0].split("=>")  # g + B1

            aether_term = aether[0] + ' 1 '
            for m in range(2):
                j = 0
                temp_reaction_piece = temp_reaction[m].strip().split('+')
                while j < len(temp_reaction_piece):
                    temp_term = temp_reaction_piece[j].strip().split(" ")
                    if m == 1:
                        temp_out_str += aether_term

                    if m == 0 and temp_term[0] == 'NULL':
                        temp_term[0] = aether[0]
                    elif m == 1 and temp_term[0] == 'NULL':
                        temp_term[0] = waste
                    else:
                        aether_term = ''

                    if len(temp_term) > 1:
                        (temp_term[0], temp_term[1]) = (temp_term[1], temp_term[0])
                        temp_out_str += temp_term[0] + " " + temp_term[1]
                    else:
                        temp_term.append("1")
                        temp_out_str += temp_term[0] + ' 1'

                    if temp_term[0] not in set(known_chems):
                        known_chems.append(temp_term[0])
                        if temp_term[0] == aether[0]:
                            temp_chems[temp_term[0]] = '1'
                        else:
                            temp_chems[temp_term[0]] = '0'

                    temp_out_str += " "
                    j += 1
                if m == 0:
                    temp_out_str += ": "

            temp_out_str = temp_out_str.strip()
            temp_out_row.append(temp_out_str + " : " + temp_rate)
        elif len(MARlea_input_lst[i]) > 0:
            temp_chem = MARlea_input_lst[i][0]
            if temp_chem not in set(known_chems) and temp_chem not in set(aether):
                known_chems.append(temp_chem)
                temp_chems[MARlea_input_lst[i][0]] = MARlea_input_lst[i][1]

    f_aleae_output_in = open_aleae_file_write(aleae_in_str)
    if f_aleae_output_in is None:
        return
    for elem in known_chems:
        f_aleae_output_in.write(elem.strip() + " " + temp_chems[elem].strip() + ' N\n')
    f_aleae_output_in.close()

    f_aleae_output_r = open_aleae_file_write(aleae_r_str)
    if f_aleae_output_r is None:
        return
    for elem in temp_out_row:
        f_aleae_output_r.write(elem + "\n")
    f_aleae_output_r.close()


def scan_args():
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

    print(waste_local)
    print(aether_local)

    if mode == Flags.A_TO_M:
        print(sys.argv[4])
        if not is_valid_flag(sys.argv[4]):
            print("Error: Invalid flag")
            print(sys.argv[4])
            exit(-1)

        if ".in" not in sys.argv[2] and not os.path.isfile(sys.argv[2]):
            print("Error: check if filepath is valid")
            exit(-1)
        if ".r" not in sys.argv[3] and not os.path.isfile(sys.argv[3]):
            print("Error: check if filepath is valid")
            exit(-1)
        if ".csv" not in sys.argv[5]:
            print("Error: Invalid output file type")
            exit(-1)

        aleae_in_str = sys.argv[2]
        aleae_r_str = sys.argv[3]
        marlea_input_str = sys.argv[5]
        write_to_marcea_out(aleae_in_str, aleae_r_str, marlea_input_str, waste_local, aether_local)
    elif mode == Flags.M_TO_A:
        if ".csv" not in sys.argv[2] and not os.path.isfile(sys.argv[2]):
            print("Error: check if filepath is valid")
            exit(-1)
        if len(sys.argv) >= 4 and not is_valid_flag(sys.argv[3]):
            print("Error: Invalid flag")
            exit(-1)
        if len(sys.argv) >= 5 and ".in" not in sys.argv[4]:
            print("Error: Invalid output file type")
            exit(-1)
        if len(sys.argv) >= 6 and ".r" not in sys.argv[5]:
            print("Error: Invalid output file type")
            exit(-1)
        if len(sys.argv) >= 7:
            if "waste=" in sys.argv[6]:
                waste_local = sys.argv[6].strip("waste=")
            else:
                print("Error: invalid name for aether and/or waste")
                exit(-1)

        marlea_input_str = sys.argv[2]
        aleae_in_str = sys.argv[4]
        aleae_r_str = sys.argv[5]
        write_to_aleae_out(marlea_input_str, aleae_in_str, aleae_r_str, waste_local, aether_local)
    else:
        print("Error: Invalid flag" + sys.argv[1])


scan_args()

# jfdksl.py -a initfile.in reactionfile.r -o filename.csv waste=W aether=S.r,S.g,S.b
# jfdksl.py -m filename.csv -o initfile.in reactionfile.r waste=W aether=S
