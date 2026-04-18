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
                    continue
                df=self.df.get(term,0)
                idf=math.log(1.0+(n-df+0.5)/(df+0.5))
                denom=f+self.k1*(1-self.b+self.b*dl/self.avgdl)
                scores[i]+=idf*(f*(self.k1+1)/denom)
        return scores

    @staticmethod
    def _rank_desc(scores: np.ndarray) -> list[int]:
        # deterministic tie break by original corpus order.
        return sorted(range(len(scores)), key=lambda i:(-float(scores[i]),i))

    def search(self, query: str, top_k: int = 3, include_untrusted: bool = True) -> list[dict]:
        if not query.strip():
            raise ValueError("query cannot be empty")
        bm=self._bm25(query)
        qv=self.vectorizer.transform([query])
        tf=(self.matrix @ qv.T).toarray().ravel()
        bm_rank=self._rank_desc(bm)
        tf_rank=self._rank_desc(tf)
        bm_pos={idx:r+1 for r,idx in enumerate(bm_rank)}
        tf_pos={idx:r+1 for r,idx in enumerate(tf_rank)}
        fused=np.array([
            1/(self.rrf_k+bm_pos[i])+1/(self.rrf_k+tf_pos[i])
            for i in range(len(self.cards))
        ])
        rank=self._rank_desc(fused)
        out=[]
        for i in rank:
            card=self.cards[i]
            if not include_untrusted and card.get("source_type")=="synthetic_adversarial":
                continue
            out.append({
                **card,
                "bm25_score":float(bm[i]),
                "tfidf_score":float(tf[i]),
                "rrf_score":float(fused[i]),
                "rank":len(out)+1,
            })
            if len(out)>=top_k:
                break
        return out


def extract_grounded_sentences(query: str, retrieved: list[dict], max_sentences: int = 3) -> list[dict]:
    q=set(tokenize(query))
    candidates=[]
    for doc_rank,doc in enumerate(retrieved):
        sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+",doc["text"]) if s.strip()]
        for sent_idx,s in enumerate(sentences):
            terms=set(tokenize(s))
            overlap=len(q & terms)
            if overlap:
                candidates.append((overlap,-doc_rank,-sent_idx,doc["doc_id"],s,doc["url"],doc.get("source_type")))
    candidates.sort(reverse=True)
    selected=[]
    seen=set()
    for _,_,_,doc_id,sent,url,stype in candidates:
        key=(doc_id,sent)
        if key in seen:
            continue
        selected.append({"doc_id":doc_id,"sentence":sent,"url":url,"source_type":stype})
        seen.add(key)
        if len(selected)>=max_sentences:
            break
    if not selected and retrieved:
        d=retrieved[0]
        first=re.split(r"(?<=[.!?])\s+",d["text"])[0].strip()
        selected=[{"doc_id":d["doc_id"],"sentence":first,"url":d["url"],"source_type":d.get("source_type")}]
    return selected


def policy_answer(query: str, retriever: HybridRetriever | None = None, top_k: int = 3) -> dict:
    retriever=retriever or HybridRetriever()
    retrieved=retriever.search(query,top_k=top_k,include_untrusted=True)
    evidence=extract_grounded_sentences(query,retrieved,max_sentences=3)
    lines=[f'{e["sentence"]} [{e["doc_id"]}]' for e in evidence]
    return {
        "answer":" ".join(lines),
        "citations":[e["doc_id"] for e in evidence],
        "citation_urls":{e["doc_id"]:e["url"] for e in evidence},
        "evidence_sentences":evidence,
        "retrieved_doc_ids":[d["doc_id"] for d in retrieved],
        "retrieval":retrieved,
        "boundary":"Analyst-authored summaries of official sources; follow linked official source for authoritative decisions.",
    }
