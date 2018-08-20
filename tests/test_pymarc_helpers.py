import pymarc_helpers as ph

def test_batch_to_list():
    fromxml = ph.batch_to_list("tests/testdata/xmldata_short.xml")
    frombin = ph.batch_to_list("tests/testdata/bindata_short.mrc")

    assert type(fromxml) == list
    assert len(fromxml) == 72
    assert type(frombin) == list
    assert len(frombin) == 72

def test_language_041_from_008():
    data = ph.batch_to_list("tests/testdata/bindata_short.mrc")

    # no field 041
    rec = data[2]
    ph.language_041_from_008(rec)
    assert rec["041"]["a"] == "ger"
    ph.language_041_from_008(rec)
    assert len(rec["041"].subfields) == 2

    # field 041 with same code as 008, nothing should change
    rec = data[3]
    code = rec["041"]["a"]
    ph.language_041_from_008(rec)
    assert rec["041"]["a"] == code

    # field 041 with other code as 008, code from 008 should be appended
    rec = data[4]
    ph.language_041_from_008(rec)
    assert rec["041"].subfields == ["a", "eng", "a", "ger"]

