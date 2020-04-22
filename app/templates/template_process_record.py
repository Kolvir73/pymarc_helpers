import pymarc
from pymarc_helpers import *

def process_record(record):
    record.add_ordered_field(
        pymarc.Field(
            tag="500",
            indicators=[" ", " "],
            subfields=["a", "Processed"]))
    return record
