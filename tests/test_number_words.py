from app.number_words import (
    build_load_spoken,
    dollars_to_words,
    int_to_words,
    load_id_to_words,
    miles_to_words,
    pieces_to_words,
    pounds_to_words,
)


def test_int_to_words():
    assert int_to_words(0) == "zero"
    assert int_to_words(24) == "twenty-four"
    assert int_to_words(925) == "nine hundred twenty-five"
    assert int_to_words(1850) == "one thousand and eight hundred fifty"
    assert int_to_words(42000) == "forty-two thousand"


def test_dollars_to_words():
    assert dollars_to_words(1850.0) == "one thousand and eight hundred fifty dollars"
    assert dollars_to_words(1.0) == "one dollar"


def test_pounds_to_words():
    assert pounds_to_words(42000) == "forty-two thousand pounds"


def test_miles_to_words():
    assert miles_to_words(925) == "nine hundred twenty-five miles"


def test_pieces_to_words():
    assert pieces_to_words(24) == "twenty-four pieces"


def test_load_id_to_words():
    assert load_id_to_words("L-1001") == "L dash one zero zero one"


def test_build_load_spoken():
    spoken = build_load_spoken(
        load_id="L-1001",
        loadboard_rate=1850.0,
        weight=42000,
        num_of_pieces=24,
        miles=925,
    )
    assert spoken["load_id"] == "L dash one zero zero one"
    assert spoken["loadboard_rate"] == "one thousand and eight hundred fifty dollars"
    assert spoken["weight"] == "forty-two thousand pounds"
    assert spoken["num_of_pieces"] == "twenty-four pieces"
    assert spoken["miles"] == "nine hundred twenty-five miles"
