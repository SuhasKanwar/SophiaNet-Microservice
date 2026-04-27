import time

import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer

from utils.logger import logger

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


class Timer:
    def __init__(self):
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.elapsed_ms = round((time.perf_counter() - self._start) * 1000, 2)


def compute_bleu(reference: str, hypothesis: str) -> float | None:
    try:
        ref_tokens = nltk.word_tokenize(reference.lower())
        hyp_tokens = nltk.word_tokenize(hypothesis.lower())
        if not ref_tokens or not hyp_tokens:
            return None
        smoothie = SmoothingFunction().method1
        return round(sentence_bleu([ref_tokens], hyp_tokens, smoothing_function=smoothie), 4)
    except Exception as e:
        logger.warning(f"BLEU computation failed: {e}")
        return None


def compute_rouge_l(reference: str, hypothesis: str) -> float | None:
    try:
        if not reference.strip() or not hypothesis.strip():
            return None
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        scores = scorer.score(reference, hypothesis)
        return round(scores["rougeL"].fmeasure, 4)
    except Exception as e:
        logger.warning(f"ROUGE-L computation failed: {e}")
        return None
