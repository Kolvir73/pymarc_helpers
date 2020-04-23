#!/usr/bin/env python3
import argparse
import sys
import copy
import os
import subprocess
import difflib
import textwrap
from runpy import run_path
from pymarc_helpers import *


TEMPLATE_DIR = "app/templates"

# Initialize parser.
parser = argparse.ArgumentParser(prog="process_marc",
                                 description="Process MARC-data from a specified input file.")


# Add the Arguments.
parser.add_argument("-i",
                    "--input-file",
                    metavar="INPUT_FILE",
                    type=str,
                    help="the source file",
                    required=True,)

parser.add_argument("-o",
                    "--output-file",
                    metavar="OUTPUT_FILE",
                    type=str,
                    help="The file to write the output to. Defaults to 'output_INPUT_FILE'. Overwrites existing files without warning.")

parser.add_argument("-f",
                    "--script-file",
                    metavar="SCRIPT",
                    type=str,
                    help="Python script to process the data. Must contain a function 'process_record(rec)' that gets applied to every record in a batch. If not given, the example script is run.")

parser.add_argument("-s",
                    "--stats",
                    action="store_true",
                    help="Print field stats of input and exit.")

parser.add_argument("--run-test",
                    action="store_true",
                    help="Output a sample of the first 20 records (or all if there are less than 20 records) data raw and cooked to separate text files.")
parser.add_argument("--run-all",
                            action="store_true",
                            help="Process the whole input file and write an output file.")

parser.add_argument("--diff",
                    action="store_true",
                    help="Make a side by side html-diff and try to open it in system application.")

parser.add_argument("--output-format",
                    choices=["bin", "xml", "text"],
                    default="xml",
                    help="Physical format of the output: MARC transmission format (bin), MARC21-XML (xml), or MARCBreaker (text) for human consumption. If not specified, xml is used.")

# Get the args from the parser.
args = parser.parse_args()

inlist = batch_to_list(args.input_file)

# import the process_record-function
if args.script_file:
    script = run_path(args.script_file)
    process_record = script["process_record"]
else:
    script = run_path(f"{TEMPLATE_DIR}/template_process_record.py")
    process_record = script["process_record"]

def get_sample(inlist):
    """Return a sample of 20 records, or all records if the inlist is shorter than 20."""

    if len(inlist) > 20:
        sample = [copy.deepcopy(rec) for rec in inlist[:20]]
    else:
        sample = [copy.deepcopy(rec) for rec in inlist]

    return sample

def diff(inlist):
    """Return a html-Diff of all records in a batch, before and after processing"""
    diff_template = open(f"{TEMPLATE_DIR}/template_diff.html").read()

    d = difflib.HtmlDiff()

    def prettify_subfields(rec):
        """Return a string representation of a record with subfields on
        new lines.
        """

        rec = str(rec)
        temp_record = ""
        pretty_record = ""
        for line in rec.split("\n"):
            temp_record += line[:9]
            temp_record += line[9:].replace("$", "\n        $")
            temp_record += "\n"

        for line in temp_record.split("\n"):
            pretty_record += textwrap.fill(line, subsequent_indent=" " * 10) + "\n"

        # hack to get fixed width
        pretty_record += " " * 82

        return pretty_record

    for rec in inlist:
        before = prettify_subfields(copy.deepcopy(rec)).split("\n")
        after = prettify_subfields(process_record(copy.deepcopy(rec))).split("\n")

        diff_template += d.make_table(before, after)

    diff= diff_template + "</body></html>"

    return diff

# name of output file
if args.output_file:
    output_file = args_output_file
else:
    input_file_tail = os.path.split(args.input_file)[-1]
    extension_idx = input_file_tail.find(".")
    outfile_base = input_file_tail[:extension_idx]
    outfile = f"{outfile_base}_output"


# return stats
if args.stats:
    print(getstats(inlist))

# make a test run and write to output files
if args.run_test:
    # get the sample
    sample = get_sample(inlist)
    # write the sample to files
    write_to_file([rec for rec in sample], f"sample_{outfile_base}_raw", "text")
    write_to_file([process_record(rec) for rec in sample], f"sample_{outfile_base}_cooked", "text")

if args.run_all:
    write_to_file([process_record(copy.deepcopy(rec)) for rec in inlist], outfile, args.output_format)

if args.diff:
    diff_file = f"diff_{outfile}.html"
    # need to specify encoding lest it fails on Windows
    with open(diff_file, "w", encoding="utf-8", newline="") as fh:
        fh.write(diff(get_sample(inlist)))
    if sys.platform == "win32":
        os.startfile(diff_file)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, diff_file])
