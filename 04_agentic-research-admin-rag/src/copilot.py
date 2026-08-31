from __future__ import annotations
import json, math, re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]+")

@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    source_type: str
    url: str
    text: str
    tags: tuple[str, ...] = ()

@dataclass
class RetrievalHit:
    doc_id: str
    title: str
    score: float
    snippet: str
    url: str
    source_type: str

@dataclass
class ToolResult:
    tool: str
    ok: bool
    result: dict[str, Any]
    refusal_reason: str | None = None

def _tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]

class HybridRetriever:
    def __init__(self, docs: list[Document]):
        self.docs = docs
        self.doc_tokens = [_tokens(d.title + " " + d.text + " " + " ".join(d.tags)) for d in docs]
        self.df: dict[str, int] = {}
        for toks in self.doc_tokens:
            for tok in set(toks):
                self.df[tok] = self.df.get(tok, 0) + 1

    def search(self, query: str, k: int = 3) -> list[RetrievalHit]:
        q = _tokens(query)
        qset = set(q)
        scored: list[tuple[float, int]] = []
        n = max(len(self.docs), 1)
        phrase = query.lower().strip()
        for i, toks in enumerate(self.doc_tokens):
            tf: dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            lexical = 0.0
            for t in qset:
                idf = math.log((n + 1) / (self.df.get(t, 0) + 1)) + 1.0
                lexical += (1 + math.log(tf[t])) * idf if t in tf else 0.0
            overlap = len(qset.intersection(toks)) / max(len(qset), 1)
            hay = (self.docs[i].title + " " + self.docs[i].text).lower()
            phrase_bonus = 1.5 if len(phrase) >= 8 and phrase in hay else 0.0
            scored.append((lexical + 2.0 * overlap + phrase_bonus, i))
        scored.sort(reverse=True)
        out = []
        for score, i in scored[:k]:
            d = self.docs[i]
            snippet = d.text[:260].strip()
            out.append(RetrievalHit(d.doc_id, d.title, round(score, 6), snippet, d.url, d.source_type))
        return out

class ResearchAdminCopilot:
    READ_ONLY_TOOLS = {"deadline_lookup", "checklist_generate", "policy_lookup", "document_compare"}
    BLOCKED_TOOLS = {"submit_application", "send_email", "change_permissions", "delete_record"}

    def __init__(self, docs: list[Document]):
        self.docs = docs
        self.retriever = HybridRetriever(docs)
        self.audit: list[dict[str, Any]] = []

    def retrieve(self, query: str, k: int = 3) -> list[RetrievalHit]:
        return self.retriever.search(query, k)

    def answer(self, query: str, k: int = 3) -> dict[str, Any]:
        hits = self.retrieve(query, k)
        citations = [h.doc_id for h in hits if h.score > 0]
        answer = " ".join(h.snippet for h in hits if h.score > 0)
        if not citations:
            answer = "Insufficient grounded evidence in the bounded corpus."
        event = {"action": "answer", "query": query, "citations": citations}
        self.audit.append(event)
        return {"answer": answer, "citations": citations, "hits": [asdict(h) for h in hits]}

    def use_tool(self, tool: str, args: dict[str, Any], approved: bool = False) -> ToolResult:
        if tool in self.BLOCKED_TOOLS and not approved:
            r = ToolResult(tool, False, {}, "explicit approval required for external/privileged action")
            self.audit.append({"action": "tool", "tool": tool, "args": args, "ok": False, "refused": True})
            return r
        if tool not in self.READ_ONLY_TOOLS and tool not in self.BLOCKED_TOOLS:
            r = ToolResult(tool, False, {}, "unknown or unsupported tool")
            self.audit.append({"action": "tool", "tool": tool, "args": args, "ok": False, "refused": True})
            return r
        if tool == "deadline_lookup":
            result = self._deadline_lookup(args)
        elif tool == "checklist_generate":
            result = self._checklist(args)
        elif tool == "policy_lookup":
            result = self.answer(str(args.get("query", "")))
        elif tool == "document_compare":
            result = self._compare(args)
        else:
            result = {"simulated": True, "note": "approved external action not executed in research demo"}
        self.audit.append({"action": "tool", "tool": tool, "args": args, "ok": True, "approved": approved})
        return ToolResult(tool, True, result)

    def _deadline_lookup(self, args: dict[str, Any]) -> dict[str, Any]:
        sponsor = str(args.get("sponsor", "")).lower()
        hits = self.retrieve(sponsor + " deadline due date submission", 2)
        return {"sponsor": sponsor, "evidence": [asdict(h) for h in hits]}

    def _checklist(self, args: dict[str, Any]) -> dict[str, Any]:
        sponsor = str(args.get("sponsor", "NSF"))
        q = sponsor + " proposal required components checklist"
        hits = self.retrieve(q, 3)
        items = []
        for h in hits:
            for term in ["project summary", "project description", "references", "budget", "data management", "biosketch"]:
                if term in h.snippet.lower() and term not in items:
                    items.append(term)
        return {"sponsor": sponsor, "items": items, "citations": [h.doc_id for h in hits]}

    def _compare(self, args: dict[str, Any]) -> dict[str, Any]:
        a = str(args.get("a", "")); b = str(args.get("b", ""))
        ta, tb = set(_tokens(a)), set(_tokens(b))
        return {"shared_terms": sorted(ta & tb), "only_a": sorted(ta - tb), "only_b": sorted(tb - ta)}

    def workflow(self, request: str) -> dict[str, Any]:
        low = request.lower()
        if any(x in low for x in ["submit", "send email", "delete", "change permission"]):
            tool = "submit_application" if "submit" in low else "send_email" if "email" in low else "delete_record" if "delete" in low else "change_permissions"
            result = self.use_tool(tool, {"request": request}, approved=False)
            return {"state": "REFUSED_PENDING_APPROVAL", "tool": asdict(result), "trace": list(self.audit)}
        if "checklist" in low:
            result = self.use_tool("checklist_generate", {"sponsor": "NSF" if "nsf" in low else "NIH"})
        elif "deadline" in low or "due date" in low:
            result = self.use_tool("deadline_lookup", {"sponsor": "NSF" if "nsf" in low else "NIH"})
        else:
            result = self.use_tool("policy_lookup", {"query": request})
        return {"state": "COMPLETED_READ_ONLY", "tool": asdict(result), "trace": list(self.audit)}


def load_corpus(path: str | Path) -> list[Document]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Document(r["doc_id"], r["title"], r["source_type"], r["url"], r["text"], tuple(r.get("tags", []))) for r in rows]
