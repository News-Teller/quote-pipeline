from pke.unsupervised import MultipartiteRank
from .config import config

class KeyphrasesExtract:
    def __init__(self, model):
        self.model = model
        self.n_best = config.core.n_keyphrases

    def get_keyphrases(self, text: str) -> list[str]:
        """Compute pke's keyphrases."""
        if not text:
            return []

        with self.model.select_pipes(disable='ner'):
            extractor = MultipartiteRank()
            extractor.load_document(text, normalization=None, spacy_model=self.model)
            extractor.candidate_selection()
            extractor.candidate_weighting()

            keyphrases = [kp.lower() for kp, _ in extractor.get_n_best(self.n_best)]
        
        return keyphrases

    def __call__(self, text: str) -> list[str]:
        return self.get_keyphrases(text)