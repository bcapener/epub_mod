import pytest

from sexdetect import sexual_probability


@pytest.mark.parametrize("text,threshold", [
    ("He masturbated in the shower.", 0.8),
    ("She gave him a blowjob.", 0.8),
    ("He watched porn until late.", 0.75),
    ("The couple made love in the candlelight.", 0.6),
    ("He fucked her on the couch.", 0.6),
    ("He fingered her on the couch.", 0.6),
    ("Her breasts heaved as she removed her lingerie.", 0.6),
    ("They had sex all night long.", 0.4),
    ("She smacked his ass playfully.", 0.4),
])
def test_explicit_sentences(text, threshold):
    assert sexual_probability(text) >= threshold


@pytest.mark.parametrize("text", [
    "The cat sat on the mat.",
    "The cock crowed at dawn.",
    "The pussy cat slept peacefully on the sofa.",
    "\"Poor Pussy,\" said Susan, stroking the cat's fur.",
    "Don't dick around with me, pal.",
    "The donkey is a little ass.",
    "They discussed sexual harassment at work.",
    "Same sex marriage is legal here.",
    "It was a tit-for-tat exchange between rivals.",
    "The recipe calls for a pinch of cumin.",
    "The book covers sexual health and reproduction.",
    "The cock was crowing and the pussies were fighting.",
    "He is a complete tool.",
    "It cost $3.50 for the whole item.",
])
def test_innocent_sentences(text):
    assert sexual_probability(text) <= 0.05


@pytest.mark.parametrize("text", [
    "What the fuck did you just say to me?",
    "Fuck you, pal.",
    "This is fucking awesome!",
    "Oh my god, that's the fucking worst.",
])
def test_curse_word_sentences_rate_low(text):
    assert sexual_probability(text) < 0.3


def test_multi_sentence_uses_max():
    text = "The rooster crowed at dawn. Then he masturbated furiously."
    assert sexual_probability(text) == pytest.approx(0.875, abs=0.001)


def test_multi_sentence_mean():
    text = "The rooster crowed at dawn. Then he masturbated furiously."
    assert sexual_probability(text, aggregate="mean") == pytest.approx(0.4375, abs=0.001)


def test_strips_html():
    assert sexual_probability("<p>He masturbated.</p>") == pytest.approx(0.875, abs=0.001)


def test_sentence_split_boundaries():
    text = "The item cost $3.50 at Mr. Smith's store. He watched porn after."
    assert sexual_probability(text) > 0.7


def test_empty_input():
    assert sexual_probability("") == 0.0
    assert sexual_probability("   ") == 0.0