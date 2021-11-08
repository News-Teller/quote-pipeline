import random
import pytest
from module import spacy_model, QuotesExtract
from module.transforms import Quote
from tests.assets import *


quotes_ids=range(0, len(QUOTES))


def add_whitepaces(text):
    whitepaces = ' \n\t'
    random.seed()

    prefix = [whitepaces[random.randint(0,2)] for _ in range(0, random.randint(0, 4))]
    suffix = [whitepaces[random.randint(0,2)] for _ in range(0, random.randint(0, 4))]

    return len(prefix), len(suffix), ''.join(prefix) + text + ''.join(suffix)


@pytest.mark.parametrize('text', QUOTES, ids=quotes_ids)
def test_quote_strip(text):
    n_prefix, n_suffix, longer_text = add_whitepaces(text)

    quote = Quote(longer_text, 0, len(longer_text))    
    quote.strip()

    # check positioning
    assert (quote.start == n_prefix) and (quote.end == (len(longer_text) - n_suffix)) 

    # check quote.strip() behaves like built-in strip
    assert quote.text == text.strip()


def test_quotes_extract_extract_quotes():
    qa = QuotesExtract(spacy_model)
    computed = qa.extract_quotes(TEXT)

    # all quotes are extracted
    assert len(computed) == len(QUOTES)

    # all extracted quotes are correct 
    for index, quote in enumerate(computed):
        assert quote.text in TEXT
        assert quote.text == QUOTES[index]
        