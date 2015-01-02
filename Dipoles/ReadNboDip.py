# -*- coding: utf-8; -*-

"""
Python script to extract dipole moment data from NBO output (*.nbo)
run from IPython shell as:
%run ReadNboDip.py form.nbo
or
%run ReadNboDip.py ./dipole/form.nbo

run from the system shell as:
python ReadNboDip.py form.nbo
or
python ReadNboDip.py ./dipole/form.nbo
"""

# author:   'Marcel Patek'
# filename: 'ReadNboDip.py'
# date:      1/1/2015
# version:  '1.0'
# email:    'chemgplus@gmail.com'
# license:  'GNU-GPL3'
# usage:     python ReadNboDip.py nbofile.nbo

'''
 * Copyright (C) 2015 Marcel Patek
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * For a copy of the GNU General Public License,
 * see <http://www.gnu.org/licenses/>.
'''

import os
import re
import sys
import pandas as pd


def print_frame_top(m, c):
    print(c * m)


def print_frame_bot(m, c):
    print(c * m)


def main(argv):
    if len(argv) < 2:
        print_frame_top(60, '+')
        sys.stderr.write("\n   Usage: >>[python] %s file *.out *.nbo\n\n" % (argv[0],))
        sys.stderr.write(
            "\n   or  : >>[python] %sy *.out\n\n" % sys.argv[0].split("\\")[len(sys.argv[0].split("\\")) - 1][0:-1])
        print_frame_bot(60, '+')
        return 1

    if not os.path.exists(argv[1]):
        print_frame_top(60, '+')
        sys.stderr.write("\n   ERROR: *.out or *.nbo file %r was not found!\n\n" % (argv[1],))
        print_frame_bot(60, '+')
        return 1

    if len(getdip(sys.argv[1])) < 1:
        print_frame_top(60, '+')
        sys.stderr.write("\n ERROR: This does not seem to be the right file. Dipole summary is missing.\n\n")
        print_frame_bot(60, '+')
        return 1

    print "\n..... Parsing the file: " + argv[1]


def getdip(infile):
    """
    Find the 'Dipole Moment' summary in *.nbo or *.out file
    :param infile: NBO/GENNBO output file
    :return: line as string containing title 'DIPOLE MOMENT ANALYSIS:'
    """
    try:
        f = open(infile, 'r')
        getdip = ''
        fi = f.readlines()
        for line in fi:
            if 'DIPOLE MOMENT ANALYSIS:' in line:
                getdip = line.split()  # splits by words
                f.close()
        return getdip
    except IOError:
        print "This does not seem to be the right file. Dipole summary is missing."


# Parse the text section of Dipole Analysis into the list 'capture'
def parseraw(filein):
    """
    Line-by-line processing of *.nbo or *.out text files
    :param filein as input file
    :return: list containing parsed raw dipole moment summary
    """
    start = 0
    begin = 0
    end = 1
    capture = []
    with open(filein, 'r') as f:
        for line in f:
            # condition to end parsing
            if begin == 1 and '-------' in line:
                end = 0
            # parse the chunk
            if start == 1 and begin == 1 and end == 1 and not ("deloc" in line):
                if re.match(r"\s$", line):  # if there's a space in the line
                    continue
                capture += [line.lstrip()]
            # First condition to initiate capture
            if 'DIPOLE MOMENT ANALYSIS:' in line:
                start = 1
            # Second condition to initiate capture
            if start == 1 and '==============' in line:
                begin = 1
    return capture


# Extract values
def getdipvalues(capture):
    """
    Line-by-line processing of the raw Dipole moment capture
    :param list capture: NBO/GENNBO output file
    :return: list containing parsed dipole details to create Pandas dataframe
    """
    orbnum = []
    orbtype = []
    dipX = []
    dipY = []
    dipZ = []
    dipTot = []
    try:
        for item in capture:
            # Regex with capturing groups to parse lines in the dipole section
            pattern = re.search(
                r'([0-9]{1,3})\.\s([A-Z]{2}.+)\s{7,13}(-?\d\.\d\d)\s?\s(-?\d\.\d\d)'
                '\s?\s(-?\d\.\d\d)\s?\s(\d\.\d\d)\s?\s.+',
                item, re.MULTILINE)
            if pattern:
                orbnum.append(pattern.group(1).strip())
                orbtype.append(pattern.group(2).strip())
                dipX.append(pattern.group(3))
                dipY.append(pattern.group(4))
                dipZ.append(pattern.group(5))
                dipTot.append(pattern.group(6))
        return orbnum, orbtype, dipX, dipY, dipZ, dipTot
    except ValueError, Argument:
        print "The argument does not contain list.\n", Argument


if __name__ == "__main__":
    # Errors in the input - get the usage and errors
    if main(sys.argv) == 1:
        raise SystemExit

# Read data in from terminal
infile = sys.argv[1]

# Save the file path, name and extension
fullpath = os.path.abspath(infile)
path, file = os.path.split(fullpath)
basename, extension = os.path.splitext(infile)

capture = parseraw(infile)

# Create Pandas dataframe
orbnum, orbtype, dipX, dipY, dipZ, dipTot = getdipvalues(capture)

# Create Pandas DataFrame
df = pd.DataFrame({'NLMO': orbnum, 'Type': orbtype, 'X': dipX, 'Y': dipY, 'Z': dipZ, 'Tot_Dip': dipTot},
                  columns=['NLMO', 'Type', 'X', 'Y', 'Z', 'Tot_Dip'])
df[['X', 'Y', 'Z', 'Tot_Dip']] = df[['X', 'Y', 'Z', 'Tot_Dip']].astype(float)
df[['NLMO']] = df[['NLMO']].astype(int)

# Printing dataframe output
print "\n"
print_frame_top(60, '+')
print df
print_frame_bot(60, '+')

# Write dataframe to .csv file
try:
    df.to_csv(basename + "_dip.csv", index=False, encoding='utf-8')
except IOError:
    print "Error: can\'t find the file or read data"
else:
    print "\n"
    print ">> Contents of the dataframe was written to " + path + "\\" + file + "_dip.csv file"
