from epub_mod import SEXUAL_CONTENT_THRESHOLD, split_sentences


def test_split_sentences_basic():
    assert split_sentences("Hello world. How are you? I am fine!") == [
        "Hello world.",
        "How are you?",
        "I am fine!",
    ]


def test_split_sentences_keeps_abbreviations():
    assert split_sentences("Dr. Jones was here. He left shortly after.") == [
        "Dr. Jones was here.",
        "He left shortly after.",
    ]


def test_split_sentences_handles_single_initial():
    assert split_sentences("J. R. R. Tolkien wrote many books. This is one.") == [
        "J. R. R. Tolkien wrote many books.",
        "This is one.",
    ]


def test_split_sentences_single_sentence():
    assert split_sentences("No punctuation here") == ["No punctuation here"]


def test_print_sexual_sentences_filters_by_threshold(capsys, monkeypatch):
    import epub_mod

    scores = iter([0.9, 0.1, 0.75, 0.74])
    monkeypatch.setattr(epub_mod, "sexual_content_probability", lambda s: next(scores))

    epub_mod.print_sexual_sentences("first. second. third. fourth.")

    out = capsys.readouterr().out.splitlines()
    assert out == ["0.900 first.", "0.750 third."]
    assert SEXUAL_CONTENT_THRESHOLD == 0.75