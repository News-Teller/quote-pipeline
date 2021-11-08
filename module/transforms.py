import re
from typing import Union
import fasttext

from .config import config

BLACKLIST = {'covid', 'covid-19'}


class Quote:
    def __init__(self, text: str, start: int, end: int) -> None:
        self.text = text
        self.start = start
        self.end = end

    def strip(self) -> None:
        """Strip quote text and update start and end positions."""
        # whitespaces on the left
        length = len(self.text)
        self.text = self.text.lstrip()
        self.start += length - len(self.text)

        # whitespaces on the right
        length = len(self.text)
        self.text = self.text.rstrip()
        self.end -= length - len(self.text)

    @staticmethod
    def is_valid(quote: object, n_words: int = 5) -> bool:
        return len(quote.text.split(" ")) >= n_words

    def  __str__(self) -> str:
        return self.text


class Entity:
    def __init__(self, name: str, start: int, end: int, paragraph_id: int) -> None:
        self.name = name
        self.start = start
        self.end = end
        self.paragraph_id = paragraph_id

    def  __str__(self) -> str:
        return self.name


class QuotesExtract():
    _spacy_components = "ner"

    def __init__(self, spacy_model):
        self.model = spacy_model
        self.paragraph_sep = "%paragraphs%|\n\n"
        
    def extract_quotes(self, text: str) -> list[Quote]:
        """Extract quotes from a text by looping on every char,
        start building a quote when an opening mark is found,
        close when the matching closing mark is found.

        While slower than a regex-based approach, this should be
        more accurate.
        """
        opening = '"«”“'
        closing = '"»“”'
        mapping = dict(zip(opening, closing))

        end_char = None
        building = False
        start_pos = -1

        quotes = []
        for pos, char in enumerate(text):
            # found an opening mark, start building a quote 
            if (not building) and (char in opening):
                start_pos = pos
                end_char = mapping[char]
                building = True

            # found matching closing mark, close quote
            elif building and (char == end_char):
                q = Quote(text[start_pos+1:pos], start_pos+1, pos-1)
                q.strip()

                if Quote.is_valid(q):
                    quotes.append(q)

                building = False
                end_char = None

            # edge case: sometimes quote ends with the paragraph
            elif building and (char == '\n'):
                if (len(text) >= pos+3) and (text[pos+1] == '\n') and (text[pos+2] in opening):
                    q = Quote(text[start_pos+1:pos], start_pos+1, pos-1)
                    q.strip()
                    
                    if Quote.is_valid(q):
                        quotes.append(q)

                    building = False
                    end_char = None

        return quotes

    def get_all_entities(self, text: str) -> Union[tuple[set[Entity], set[Entity], set[Entity]], tuple[None, None, None]]:
        doc = None

        with self.model.select_pipes(enable=self._spacy_components):
            doc = self.model(text)

        if doc == None:
            return (None, None, None)

        per = []
        org = []
        loc = []
        for e in doc.ents:
            if e.text.lower() in BLACKLIST:
                continue

            entity = Entity(e.text, e.start_char, e.end_char, self.get_paragraph_id(e.start_char, e.end_char, e.text, text))
            if e.label_ == "PER":
                per.append(entity)
            elif e.label_ == "ORG":
                org.append(entity)
            elif e.label_ in ["LOC", "GPE"]:
                loc.append(entity)
        
        return (list(set(per)), list(set(org)), list(set(loc)))

    def associate_quote_speaker(self, article: str, quotes: list[Quote], pers: set[Entity]) -> list[tuple[Quote, Entity]]:
        result = []
        for quote in quotes:
            paragraph_id = self.get_paragraph_id(quote.start, quote.end, quote.text, article)
            persons = list(filter(lambda x: x.paragraph_id == paragraph_id, pers))
            quote_median = quote.start + (quote.end - quote.start)/2.0
            best_dist = float("inf")
            speaker = None
            for p in persons:
                person_median = p.start + (p.end - p.start)/2.0
                dist = abs(quote_median - person_median)
                if dist < best_dist:
                    best_dist = dist
                    speaker = p
            
            result.append((quote, speaker))
        if len(result) > 0:
            return result
        else:
            return []

    def get_paragraph_id(self, s: int, e: int, quote: str, text: str) -> int:
        paragraphs = re.split(self.paragraph_sep,text)
        previous_len = 0
        for i, p in enumerate(paragraphs):
            start = previous_len
            end = previous_len + len(p) + len(self.paragraph_sep)
            previous_len = end
            if (quote in p) & (s >= start) & (s < end) & (e <= end) & (e > start):
                return i

    def transform(self, x: str) -> list[tuple[Quote, Entity]]:
        quotes = self.extract_quotes(x)
        pers, _, _ = self.get_all_entities(x)
        associated_quotes = self.associate_quote_speaker(x,quotes,pers)
        
        # convert objects to strings
        name_mapping = QuotesExtract._clean_speaker_names([s.name for s in pers])
        associated_quotes = [[q.text, name_mapping[s.name]] for q,s in associated_quotes if s != None]
        
        return associated_quotes

    def __call__(self, x: str) -> list[tuple[Quote, Entity]]:
        return self.transform(x)

    @staticmethod
    def _clean_speaker_names(speakers: list) -> Union[dict, None]:
        if len(speakers) == 0:
            return {}
        elif len(speakers) == 1:
            return { speakers[0]: speakers[0]}

        mapping = {}
        for p1 in speakers:
            added = False
            for p2 in speakers:
                if p1.lower() == p2.lower():
                    continue
                if p1.lower() in p2.lower():
                    mapping[p1] = p2
                    added = True
            
            if not added:
                mapping[p1] = p1
        
        return mapping

    
class FastText():
    def __init__(self):
        self.max_char = config.core.max_char
        self.model = fasttext.load_model(config.core.fasttext_path)

    def transform(self, x: str) -> str:
        text = x.replace("\n", " ")
        label = self.model.predict(text[:self.max_char])
        
        # Original label is like '__label__climat'
        return label[0][0][9:]
            
    def __call__(self, x: str) -> str:
        return self.transform(x)
    
   
