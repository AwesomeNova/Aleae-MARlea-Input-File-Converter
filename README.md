## Brief Description
A Python script that converts Aleae text files to a MARlea csv file and vice versa. It serves as a complementary piece of software for anyone to convert input files to run a chemical reaction network on either Aleae or MARlea. 

The program takes either an MARlea file or an Aleae .r reaction and .in init files as input, and it converts it to the desired format. All input files must be valid as specified by Aleae and MARlea, as Aleae or MARlea can accept it and run the chemical reaction without an error causing an exit. During the conversion process, the script checks for whether an input file given to it is valid, specified by the documentation for Aleae and MARlea.

## Motivation
The script was created to automate the laborious task of converting MARlea files into Aleae files by hand or assisted with the find-and-replace tool. Converting by hand was tedious and time-consuming, especially with files with several lines of reactions. This was created as a way to save time, effort, and sanity. 

File conversions are done mainly to take advantage of a simulator's strengths and features while avoiding the other's weaknesses. Aleae, created by Marc Riedel, contains useful features for simulating chemical reaction networks. It has a settings for the number of trials, time limits, threshold for specified chemicals, outputs to the terminal adjustable via a setting, and step limits. However, it has poor performance, it requires two text files as input, and it has difficult-to-parse and unintuitive syntax at first glance. All of these problems makes using Aleae frustrating to use, so an alternative was created. 

Created by then-student Marceline Sorenson, MARlea improved upon Aleae in terms of performance and ease of use. It has much better performance, has a simple intuitive syntax that resembles notation for chemical reactions (only requires one csv file as an input), and displays the result of the CRN in a easy-to-read format. Despite the improvements, the latest release only has a setting for the number of trial and lack the other features Aleae has like thresholds.

Due to the differences between Aleae and MARlea, converting files between their respective formats is valuable to have for simulating chemical reaction network in a laboratory setting or for EE 5393.

## Key Concepts
According to Marc Riedel's model of computational chemical reactions, a chemical can be created from nothing or from the "aether," or is destroyed and turned to "waste." These concepts are implemented as features of MARlea, but not of Aleae. They are represented below:
* waste: 
  * Aleae: X 1 : W 1 : 100
  * MARlea: X => NULL, 100
* aether:
  * Aleae: S.a 1 : S.a 1 X 1 : 100
  * MARlea: NULL => X, 100

## Limitations 
* Due to difference between Aleae and MARlea files, conversions between them requires certain information to be lost
  * Names of "aether" chemicals as well as threshhold settings in Aleae files are lost when converting them to MARlea files
  * Comments in MARlea files are discarded when converting them to Aleae files

## System Requirements and Recommendations
* Python 3.8 or higher Required (Latest Recommended)
* Preferred IDE to Run Script Recommended
 
## Command-Line Input
To operate the script, commands are entered into the terminal in this format:

```python converter.py <mode-cmd> <--input> <input file(s)> [--pipeline_enable] <--output> <output-file(s)> [--waste] [--aether]```

### Commands
* a-to-m: convert Aleae files into a MARlea file
* m-to-a: convert MARlea file to Aleae files
* gui: summon the gui

### Required Flags
* --input, -i: precedes input file name(s)
* --output, -o: precedes output file name(s)

### Optional Flags
* [--pipelined_enable], -p: enables pipelined execution
* [--waste]: denotes from what chemical to convert to NULL and vice versa
* [--aether]: denotes from what chemical(s) to convert to NULL and vice versa

### Example Commands
```python converter.py a-to-m -i init.in react.r -o MARlea_crn.csv --waste W --aether S.1 S.2 S.3```

```python converter.py m_to_a -i MARlea_crn.csv -p -e -o init.in react.r --waste garbo --aether S.1```

```python converter.py gui```

## Changelog
* May 15, 2024
  * 1.0: 
    * Created converter
  * 1.0.1: 
    * Fixed potential bug at for loop within convert_aleae_to_marlea() tasked with swapping chem with coefficient
* May 27, 2024
  * 1.0.2: 
    * Refactored error checking code in scan_args(), refactored and changed file opening functions to shift file checking to said functions, and added enums for parts of chemical reactions
* August 20, 2024
  * 1.0.3: 
    * Lightly simplified logic pertaining to adding aether term to chem_reaction_str
* October 3, 2024
  * 1.0.4: 
    * Fixed MARlea comments occasionally being written to .in files when converting MARlea files or Aleae files
  * 1.0.5:
    * Fixed error in the condition for the while loop in convert_aleae_to_marlea()
    * Removed redundant functions that open files for reading and replaced them with one function open_file_read()
* October 6, 2024
  * 1.1: 
    * Rewrote file reading, writing, and conversion subroutines to implement pipelined execution via threads
    * Replaced hard-coded sys.argv indices with IntEnums
    * Added flags to enable either sequential or pipelined execution
* October 7, 2024
  * 1.1.1:
    * Rewrote command-line parsing using the argparse Python library
    * Altered commands to accommodate change in command-line parsing
    * Fixed a NoneType indexing attempt bug in the MARlea-to-Aleae converter when no aether chemical is specified
* October 12, 2024
  * 1.2: 
    * Added optional pre-conversion error checking to converter.py 
    * Added error checking script with the same code used in converter.py
* October 18, 2024
  * 1.3:
    * Implemented the gui that is summoned with a command
* March 15, 2025
  * 1.4:
    * Replaced conversion logic with a parser for Aleae and MARlea, complete with mid-execution error checking
    * Removed all other error checking code

## Potential Feature(s) to Be Added
* Parallize pipelined execution
  * Can be done via multiprocessing, asyncio, and new subinterpreters modules.
  * Disabling the GIL 
    * Is possible since no concurrent write accesses to files and objects like strings
    * Concurrent access to thread-safe data structures like queues are present, so no race conditions occur.
* Support for converting non-csv input MARlea files into Aleae output files (if new files types are supported in MARlea)
