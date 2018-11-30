#!/bin/python3

import pymarc
import texttable as TT
from pymarc_helpers.code_dicts import *

class WrongFieldError(Exception):
    pass

def batch_to_list(infile):
    """Take a filename of a marc-file and return a list of pymarc.Record objects."""
    record_list = []
    with open(infile, "rb") as fh:
        # check if its xml or binary
        firstline = fh.readline()
        # set the pointer back to the beginning
        fh.seek(0)
        if firstline.startswith(b"<?xml version"):
            reader = pymarc.parse_xml_to_array(fh)
        else:
            # default: utf8_handling="strict"
            reader = pymarc.MARCReader(fh)
        for record in reader:
            record_list.append(record)
    return record_list


def getstats(record_list, filename=None):
    """Create some rudimentary stats and write them to a file. If no filename
    is specified, write the output to stdo.

    Output contains a count of records in a batch and a table with occurrences
    of fields and occurring subfields.
    """
    count = 0
    # Table for stats
    table = TT.Texttable()
    # Table for field stats
    field_table = TT.Texttable()
    field_table.header(["Tag", "Count", "Subfields"])
    field_table.set_deco(TT.Texttable.HEADER)
    field_table.set_cols_dtype(["t", "i", "t"])
    field_table.set_cols_align(["l", "r", "l"])

    fieldstat = {}
    for record in record_list:
        count += 1
        for field in record:
            if field.is_control_field():
                fieldstat[field.tag] = fieldstat.get(field.tag, [0, []])
                fieldstat[field.tag][0] += 1
            else:
                tag = field.tag + field.indicators[0].replace(
                    " ", "#") + field.indicators[1].replace(" ", "#")
                fieldstat[tag] = fieldstat.get(tag, [0, []])
                fieldstat[tag][0] += 1
                subfields = field.subfields
                for i in range(0, len(subfields), 2):
                    # subfield codes are evey other element in the list
                    if subfields[i] not in fieldstat[tag][1]:
                        fieldstat[tag][1].append(subfields[i])
                    else:
                        continue

    for tag in sorted(fieldstat):
        field_table.add_row(
            [tag, fieldstat[tag][0], sorted(fieldstat[tag][1])])

    table.add_row(["No. of records", count])

    if filename is None:
        print(table.draw() + "\n\n" + field_table.draw())
    else:
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(table.draw())
            fh.write("\n\n")
            fh.write(field_table.draw())


def write_to_file(reclist, filename="output", form="bin"):
    """write records to file"""
    if form == "bin":
        filename = filename + ".mrc"
        with open(filename, "wb") as out:
            for record in reclist:
                out.write(record.as_marc())
    elif form == "xml":
        filename = filename + ".xml"
        writer = pymarc.XMLWriter(open(filename, "wb"))
        for record in reclist:
            writer.write(record)
        writer.close()
    elif form == "text":
        filename = filename + ".txt"
        with open(filename, "wt") as out:
            writer = pymarc.TextWriter(out)
            for record in reclist:
                writer.write(record)

def change_control_data(field, pos, value):
    """Change values in control fields."""
    if not field.is_control_field():
        return
    positions = pos.split("-")
    if len(positions) > 2:
        # TODO exception
        return
    # TODO checken, ob len(data) == endpos - startpos + 1
    startpos = int(positions[0])
    endpos = int(positions[-1])
    outdata = field.data[:startpos] + value + field.data[endpos + 1:]
    field.data = outdata


def sort_subfields(subfields):
    """Return a sorted list of subfields.

    Takes a list as input. The list has to have the form
    ["code", "value", "code", "value"] eg.
    ['a', 'titel', 'c', 'verantwortlichkeitsangabe', 'b', 'zusatz']

    """
    sorted_subfields = []
    # make a list of (code, value)-tuples
    tuple_list = [(subfields[i], subfields[i + 1])
                  for i in range(0, len(subfields), 2)]
    # sort the tuple list and append to sorted subfields
    for code, value in sorted(tuple_list):
        sorted_subfields.append(code)
        sorted_subfields.append(value)
    return sorted_subfields


def remove_isbd(field):
    """Remove ISBD-punctuation at the end of the subfields.

    Takes a field object and changes it in-place.
    """
    isbd_chars = (".", ",", ":", ";", "/")
    inlist = field.subfields
    outlist = []
    for subfield in inlist:
        if subfield.rstrip().endswith(isbd_chars):
            outlist.append(subfield.rstrip()[:-1].rstrip())
        else:
            outlist.append(subfield)
    field.subfields = outlist


def insert_nonfiling_chars(field):
    """Insert nonfiling characters in 245 $$a according to the second indicator
    and set the second indicator to 0.

    Argument: a pymarc.Field object of a field 245.
    """

    # raise an error if a field othen than 245 is passed to this function
    if field.tag != "245":
        raise WrongFieldError("Nonfiling chars can only be inserted in field 245.")

    num_chars = int(field.indicators[1])
    if num_chars is 0:
        return
    else:
        sfa = field["a"]
        new_sfa = "<<" + sfa[:num_chars - 1] + ">>" + sfa[num_chars - 1:]
        field["a"] = new_sfa
        field.indicators[1] = "0"


def relator_terms_to_codes(field):
    """Replace $$e with a MARC relator term with a $$4 with the corresponding code."""
    if field["e"]:
        relator_term = field["e"].strip().lower()
        if relator_term in relators_by_name.keys():
            field.add_subfield("4", relators_by_name[relator_term])
            field.delete_subfield("e")
        else:
            print(f"Unknown relator term: {relator_term}")
    else:
        return


def language_041_from_008(record):
    """Add a field 041##$$a with the language code from 008/35-37. If 041
    already exists, append subfield $$a with the code, if not already present.
    """
    lang = record["008"].data[35:38]
    if not record["041"]:
        record.add_ordered_field(
            pymarc.Field(
                tag="041",
                indicators=[" ", " "],
                subfields=["a", lang]
            ))
    else:
        if not lang in record["041"].value():
            record["041"].add_subfield("a", lang)


def country_044_from_008(record):
    """Add a field 044##$$c with the ISO 3166-Codes derived from 008/15-17.

    All codes for USA, Canada and Great Britain are normalized to XD-US, XD-CA
    and XA-GB.
    """
    country008 = record["008"].data[15:18].rstrip()
    country044 = None
    if country008 in country_codes_marc2iso:
        country044 = country_codes_marc2iso[country008]

    if country044 is not None:
        if not record["044"]:
            record.add_ordered_field(
                pymarc.Field(
                    tag="044",
                    indicators=[" ", " "],
                    subfields=["c", country044]
                ))
        elif country044[3:] in record["044"].subfields:
            # change existing code to code with continental prefix
            if not country044 in record["044"].subfields:
                subfields = []
                for subfield in record["044"].subfields:
                    subfields.append(subfield.replace(country044[3:], country044))
                record["044"].subfields = subfields
        else:
            record["044"].add_subfield("c", country044)

def translate_ill(rec):
    """Translate 300 $$c to german."""
    if rec["300"]["b"]:
        ills = rec["300"]["b"].split(", ")
        outlist = []
        for ill in ills:
            if ill.lower() in illustration_terms:
                if illustration_terms[ill.lower()] is None:
                    continue
                else:
                    outlist.append(illustration_terms[ill.lower()])
            else:
                outlist.append(ill)
        outstring = ", ".join(outlist)
        rec["300"]["b"] = outstring


def process_data(data, process_function, test=False, output_format="bin"):
    """takes an infile and a function as arguments. process_function has to take a
    record as input and return the modified record.
    """
    outlist = []
    # check if data is a list or a filename. If it's not a list,
    # create one from the file
    if type(data) is list:
        reclist = data
    else:
        reclist = batch_to_list(data)

    # shorten the list and cange outfile-names for testing
    if test is True:
        reclist = reclist[:10]
        outfile = "TEST_loadfile"
        instats = "TEST_infile_stats.txt"
        outstats = "TEST_outfile_stats.txt"
    else:
        outfile = "loadfile"
        instats = "infile_stats.txt"
        outstats = "outfile_stats.txt"

    # stats before processing
    getstats(reclist, instats)
    # process each record in the list and append it to outlist
    for record in reclist:
        outlist.append(process_function(record))

    write_to_file(outlist, filename=outfile, form=output_format)

    # stats after processing
    # FIXME Don't hardcode file extension here
    getstats(batch_to_list(outfile + ".mrc"), outstats)
