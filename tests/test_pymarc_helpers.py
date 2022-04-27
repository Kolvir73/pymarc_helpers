import pickle
import pytest
import pymarc_helpers as ph
import pymarc

def test_batch_to_list():
    fromxml = ph.batch_to_list("tests/testdata/xmldata_short.xml")
    frombin = ph.batch_to_list("tests/testdata/bindata_short.mrc")

    assert type(fromxml) == list
    assert len(fromxml) == 72
    assert type(frombin) == list
    assert len(frombin) == 72


def test_change_control_data():
    pass


def test_sort_subfields():
    unsorted_field = pymarc.Field(
        tag="999",
        indicators=["1", " "],
        subfields=["x", "Subfield x", "a", "Subfield a1", "4", "Subfield 4", "a", "Subfield a2"]
        )

    assert ph.sort_subfields(unsorted_field.subfields) == ["4", "Subfield 4", "a", "Subfield a1", "a", "Subfield a2", "x", "Subfield x"]

def test_remove_isbd():
    # normal ISBD
    isbd_field = pymarc.Field(
        tag="245",
        indicators=["1", "0"],
        subfields=["a", "Haupttitel :", "b",
                   "Titelzusatz = Paralleltitel : Titelzusatz /",
                   "c", "Verantwortlichkeitsangabe"]
    )

    ph.remove_isbd(isbd_field)
    assert isbd_field.subfields == ["a", "Haupttitel", "b",
                   "Titelzusatz = Paralleltitel : Titelzusatz",
                   "c", "Verantwortlichkeitsangabe"]

    # TODO add corner cases


def test_insert_nonfiling_chars():
    fields = pickle.load(open("tests/testdata/245.pickle", "rb"))

    for field in fields[:3]:
        ph.insert_nonfiling_chars(field)

    f245_1, f245_2, f245_3, f264 = fields

    assert f245_1[
        "a"] == "<<Die>> österreichisch-ungarische Monarchie in Wort und Bild"
    assert f245_1.indicators == ["0", "0"]
    assert f245_2["a"] == "<<L'>>apostrophe zu Testzwecken"
    assert f245_2.indicators == ["0", "0"]
    assert f245_3[
        "a"] == '<<">>Anführungszeichen" die man übergehen will (warumauchimmer)'
    assert f245_3.indicators == ["0", "0"]

    with pytest.raises(ph.WrongFieldError):
        ph.insert_nonfiling_chars(f264)


def test_relator_terms_to_codes():
    # unknown term in $$e -> do nothing
    f100 = pymarc.Field(
        tag="100",
        indicators=["1", " "],
        subfields=["a", "Mustermann, Martin", "e", "10445599", "4", "aut"])

    ph.relator_terms_to_codes(f100)
    assert f100.subfields == [
        "a", "Mustermann, Martin", "e", "10445599", "4", "aut"
    ]

    # known term in $$e
    f100 = pymarc.Field(tag="100",
                        indicators=["1", " "],
                        subfields=["a", "Mustermann, Martin", "e", "author"])

    ph.relator_terms_to_codes(f100)
    assert f100.subfields == ["a", "Mustermann, Martin", "4", "aut"]

    # known code in $$e, corresponding term in $$4
    f100 = pymarc.Field(
        tag="100",
        indicators=["1", " "],
        subfields=["a", "Mustermann, Martin", "e", "author", "4", "aut"])

    ph.relator_terms_to_codes(f100)
    assert f100.subfields == ["a", "Mustermann, Martin", "4", "aut"]


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


def test_country_044_from_008():
    pass


def test_get_copyright():
    pass


def test_translate_ill():
    pass
