from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "data" / "corpus" / "public_source_cards.jsonl"

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP = {
    "a","an","and","are","as","at","be","by","for","from","has","have","how",
    "i","if","in","is","it","of","on","or","that","the","their","this","to",
    "what","when","where","which","who","with","do","does","my","our","can"
}


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOP]


def load_cards(path: Path = CORPUS_PATH) -> list[dict]:
    cards=[]
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            cards.append(json.loads(line))
    ids=[c["doc_id"] for c in cards]
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate doc_id in corpus")
    return cards


class HybridRetriever:
    def __init__(self, cards: list[dict] | None = None, k1: float = 1.5, b: float = 0.75, rrf_k: int = 60):
        self.cards=cards or load_cards()
        self.k1=k1
        self.b=b
        self.rrf_k=rrf_k
        self.docs=[f'{c["title"]}. {c["sponsor"]}. {c["text"]}' for c in self.cards]
        self.tokens=[tokenize(x) for x in self.docs]
        self.lengths=np.array([len(x) for x in self.tokens],dtype=float)
        self.avgdl=float(self.lengths.mean()) if len(self.lengths) else 1.0
        self.df=Counter()
        for toks in self.tokens:
            self.df.update(set(toks))
        self.vectorizer=TfidfVectorizer(tokenizer=tokenize, preprocessor=None, token_pattern=None, lowercase=False, ngram_range=(1,2))
        self.matrix=self.vectorizer.fit_transform(self.docs)

    def _bm25(self, query: str) -> np.ndarray:
        q=tokenize(query)
        scores=np.zeros(len(self.cards),dtype=float)
        n=len(self.cards)
        for i,toks in enumerate(self.tokens):
            tf=Counter(toks)
            dl=max(1.0,self.lengths[i])
            for term in q:
                f=tf.get(term,0)
                if not f:
