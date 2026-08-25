from scripts.generate_audio import split_into_turns


def test_splits_a_simple_two_speaker_exchange() -> None:
    turns = split_into_turns("A: Hi! What's your name? B: Hi, I'm Marco.")

    assert turns == [("A", "Hi! What's your name?"), ("B", "Hi, I'm Marco.")]


def test_a_literal_em_dash_inside_a_turn_is_not_mistaken_for_a_speaker_change() -> None:
    # The turn separator is also an em dash, so a turn's own text containing
    # one ("...my friend Mark — he's a doctor") must not get split in half.
    transcript = (
        "A: So, what do you do, Anna? — B: I'm a student. And you? — "
        "A: I'm a teacher. Where do you live? — B: I live in Warsaw. "
        "How old are you, if you don't mind me asking? — "
        "A: I'm 28. And this is my friend Mark — he's a doctor."
    )

    turns = split_into_turns(transcript)

    assert turns == [
        ("A", "So, what do you do, Anna?"),
        ("B", "I'm a student. And you?"),
        ("A", "I'm a teacher. Where do you live?"),
        ("B", "I live in Warsaw. How old are you, if you don't mind me asking?"),
        ("A", "I'm 28. And this is my friend Mark — he's a doctor."),
    ]


def test_strips_the_leading_transcript_label() -> None:
    turns = split_into_turns("Transcript — A: Hi! B: Hello.")

    assert turns == [("A", "Hi!"), ("B", "Hello.")]
