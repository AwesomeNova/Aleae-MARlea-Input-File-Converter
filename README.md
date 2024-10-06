## Brief Description
A Python script that converts Aleae text files to a MARlea csv file and vice versa. It serves as a complementary piece of software for anyone to convert input files to run a chemical reaction network on either Aleae or MARlea. 

The program takes either an MARlea file or an Aleae .r reaction and .in init files as input, and it converts it to the desired format. All input files must be valid as specified by Aleae and MARlea, as Aleae or MARlea can accept it and run the chemical reaction without an error causing an exit. The script itself DOES NOT check for syntax and assumes that given input files are valid. Giving the script invalid input files may lead to unintended effects.

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
* All files given as inputs are not checked for their validity
  * Any invalid file can be inputted, which may result in unexpected outputs

## System Requirements and Recommendations
* Python 3.10 or higher Required (Latest Recommended)
* Preferred IDE to Run Script Recommended
 
## Command-Line Input

To operate the script, commands are entered into the terminal in this format:

```python converter.py <mode flag> <input files> <--output> <output file> [waste] [aether]```

### Flags

* --a_to_m, -a: convert Aleae files into a MARlea file
* --m_to_a, -m: convert MARlea file to Aleae files
* --output, -o: precedes output file name(s), selects sequential execution
* --pipelined_output, -p: precedes output file name(s), selects pipelined execution

### Options
* [waste]: denotes from what chemical to convert to NULL and vice versa
* [aether]: denotes from what chemical(s) to convert to NULL and vice versa

### Example Commands
```python converter.py --a_to_m init.in react.r --output MARlea_crn.csv [waste=W] [aether=[S.1,S.2,S.3]]```

```python converter.py --m_to_a MARlea_crn.csv --pipelined_output init.in react.r [waste=garbo] [aether=S.1]```

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
    * Fixed MARlea comments occassionally being written to .in files when converting MARlea files or Aleae files
  * 1.0.5:
    * Fixed error in the condition for the while loop in convert_aleae_to_marlea()
    * Removed redundant functions that open files for reading and replaced them with one function open_file_read()
* October 6, 2024
  * 1.1: 
    * Rewrote file reading, writing, and conversion subroutines to implement pipelined execution via threads
    * Replaced hard-coded sys.args indices with IntEnums
    * Added flags to enable either sequential or pipelined execution
