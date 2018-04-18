#!/bin/python3

import pymarc
import texttable as TT

# shortcuts for testing
bindata = "tests/testdata/bindata.mrc"
xmldata = "tests/testdata/xmldata.xml"


def batch_to_list(infile):
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
    """Creates some rudimentary stats and writes them to a file. If no filename
    is specified, the output is written to stdo.

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
                tag = field.tag + field.indicators[0].replace(" ", "#") + field.indicators[1].replace(" ", "#")
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
        field_table.add_row([tag, fieldstat[tag][0], sorted(fieldstat[tag][1])])

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
    if form is "bin":
        filename = filename + ".mrc"
        with open(filename, "wb") as out:
            for record in reclist:
                out.write(record.as_marc())
    elif form is "xml":
        filename = filename + ".xml"
        header = b"""<?xml version="1.0" encoding="UTF-8" ?>
<?xml-stylesheet type="text/xsl" href="MARC21slim2HTML.xsl" ?>
<collection xmlns="http://www.loc.gov/MARC21/slim"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.loc.gov/MARC21/slim
    http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">"""
        pass

def process_data(data, process_function, test=False, output_format="bin"):
    """takes an infile and a function as arguments. process_function has to take a
    record as input and return the modified record.
    """

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
        reclist = batch_to_list(data)
        outfile = "loadfile"
        instats = "infile_stats.txt"
        outstats = "outfile_stats.txt"

    # stats before processing
    getstats(reclist, instats)
    # process each record in the list and append it to outlist
    for record in reclist:
        process_function(record)

    # stats after processing
    getstats(reclist, outstats)

    write_to_file(reclist, filename=outfile, form=output_format)

