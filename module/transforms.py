import re
from typing import Iterable, Union
import spacy
import fasttext
from .config import config


class Quote:
    def __init__(self, text: str, start: int, end: int) -> None:
        self.text = text
        self.start = start
        self.end = end
        
    def  __repr__(self) -> str:
        return self.text


class Entity:
    def __init__(self, name: str, start: int, end: int, paragraph_id: int) -> None:
        self.name = name
        self.start = start
        self.end = end
        self.paragraph_id = paragraph_id

    def  __repr__(self) -> str:
        return self.name


class QuotesExtract():
    def __init__(self):
        self.model = spacy.load(config.core.spacy_model,
                                disable=['parser', 'tagger', 'textcat'])
        self.pattern = "[\"|«|”|“][(\.\'\;\,\’)\w\s*]+[\"|»|”|“]"
        
        self.paragraph_sep = "%paragraphs%|\n\n"
        
    def extract_quotes(self, text: str) -> list[Quote]:
        quotes = re.finditer(self.pattern, text)
        valid_quotes = []
        for q in quotes:
            quote = Quote(q.group(), q.start(), q.end())
            is_valid_quote = len(quote.text.split(" ")) >= 5
            if is_valid_quote:
                valid_quotes.append(quote)
        return valid_quotes
    
    def get_all_entities(self, text: str) -> Union[tuple[set[Entity], set[Entity], set[Entity]], tuple[None, None, None]]:
        doc = None
        doc = self.model(text)

        if doc == None:
            return (None, None, None)

        per = []
        org = []
        loc = []
        for e in doc.ents:
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
        associated_quotes = [[q.text, s.name] for q,s in associated_quotes if s != None]

        return associated_quotes

    def __call__(self, x: str) -> list[tuple[Quote, Entity]]:
        return self.transform(x)
    
    
class FastText():
    def __init__(self):
        self.max_char = config.core.max_char
        self.model = fasttext.load_model(config.core.fasttext_path)

    def transform(self, x: str) -> str:
        label = self.model.predict(x[:self.max_char])
        
        return label[0][0][9:]
            
    def __call__(self, x: str) -> str:
        return self.transform(x)
    
   
